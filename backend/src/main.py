import argparse
import locale
import os
import sys

# Forzar LC_NUMERIC="C" para evitar que Qt/Protobuf falle al parsear números flotantes con punto en locales hispanos/europeos
os.environ["LC_NUMERIC"] = "C"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"
os.environ["PADDLE_PDX_EAGER_INIT"] = "False"
try:
    locale.setlocale(locale.LC_NUMERIC, "C")
except Exception:
    pass

# Shim temprano de importlib.metadata para bundle de PyInstaller
try:
    import importlib.metadata

    _orig_version = importlib.metadata.version
    _known_versions = {
        "pyclipper": "1.4.0",
        "shapely": "2.2.0",
        "opencv-contrib-python": "4.10.0",
        "opencv-python": "4.10.0",
        "paddlex": "3.7.2",
        "paddleocr": "3.7.0",
        "pypinyin": "0.55.0",
        "jieba": "0.42.1",
        "tqdm": "4.70.0",
        "paddlepaddle": "3.3.1",
    }

    def _safe_metadata_version(pkg: str) -> str:
        try:
            return _orig_version(pkg)
        except Exception:
            if pkg in _known_versions:
                return _known_versions[pkg]
            raise

    importlib.metadata.version = _safe_metadata_version
except Exception:
    pass

import webview

from adapters.cache_sqlite import SqliteTranslationCache
from adapters.ocr_paddle import PaddleOcrAdapter, _patch_paddlex_for_pyinstaller
from adapters.pdf_pymupdf import PyMuPdfAdapter
from adapters.pinyin_jieba import PinyinJiebaAdapter
from adapters.translator_api import (
    FreeWebTranslatorAdapter,
    GeminiTranslatorAdapter,
)
from bridge.desktop_facade import DesktopFacade
from core.logger import get_logger, setup_logger
from use_cases.process_document import ProcessDocumentUseCase
from use_cases.translate_token import TranslateTokenUseCase

# Inicializar parches tempranos de entorno para PaddleX y PyInstaller
_patch_paddlex_for_pyinstaller()

logger = get_logger("main")


def load_dotenv_safely() -> None:
    """Carga variables desde archivo .env si existe sin requerir dependencias externas."""
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"),
    ]
    for env_path in candidates:
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k and k not in os.environ:
                                os.environ[k] = v
                logger.info("Variables de entorno cargadas desde: %s", env_path)
                break
            except Exception as e:
                logger.debug("No se pudo leer .env en %s: %s", env_path, e)


def _patch_pywebview_qt() -> None:
    """Corrige bug de pywebview en PyQt6 donde setFeaturePermission recibe int en vez de PermissionPolicy."""
    try:
        from PyQt6.QtWebEngineCore import QWebEnginePage
        from webview.platforms import qt

        def safe_onFeaturePermissionRequested(self, url, feature):
            try:
                self.setFeaturePermission(
                    url,
                    feature,
                    QWebEnginePage.PermissionPolicy.PermissionGrantedByUser,
                )
            except Exception as ex:
                logger.debug("Error controlado en setFeaturePermission: %s", ex)

        qt.BrowserView.WebPage.onFeaturePermissionRequested = safe_onFeaturePermissionRequested
        logger.debug("Parche PyQt6 aplicado exitosamente a pywebview onFeaturePermissionRequested.")
    except Exception as e:
        logger.debug("No se aplicó parche pywebview Qt: %s", e)


def get_frontend_url(is_dev: bool = False, dev_url: str = "http://localhost:5173") -> str:
    """Determina la URL o archivo index.html para cargar en la ventana."""
    if is_dev:
        logger.info("Modo de desarrollo activado. Cargando interfaz desde: %s", dev_url)
        return dev_url

    # Modo empaquetado con PyInstaller
    if hasattr(sys, "_MEIPASS"):
        bundled_index = os.path.join(sys._MEIPASS, "frontend_dist", "index.html")
        if os.path.exists(bundled_index):
            logger.info("Modo empaquetado PyInstaller. Cargando bundle: %s", bundled_index)
            return bundled_index

    # Modo producción local (frontend/dist/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    dist_index = os.path.join(project_root, "frontend", "dist", "index.html")

    if os.path.exists(dist_index):
        logger.info("Frontend compilado detectado en producción local: %s", dist_index)
        return dist_index

    # Fallback si no está compilado: cargar dev
    logger.warning("No se encontró bundle estático en dist/. Recurriendo a fallback dev_url: %s", dev_url)
    return dev_url


def create_facade() -> DesktopFacade:
    """Construye e inyecta las dependencias de la aplicación (Clean Architecture)."""
    logger.info("Iniciando inyección de dependencias para Clean Architecture...")
    load_dotenv_safely()

    pdf_extractor = PyMuPdfAdapter()
    segmenter = PinyinJiebaAdapter()
    ocr_engine = PaddleOcrAdapter(segmenter=segmenter)
    cache = SqliteTranslationCache(db_path="translations.db")

    # Si hay clave GEMINI_API_KEY se usa Gemini, si no el traductor gratuito en línea
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key:
        logger.info("Clave GEMINI_API_KEY detectada. Utilizando adaptador GeminiTranslator con respaldo web.")
        translator = GeminiTranslatorAdapter(api_key=api_key)
    else:
        logger.info(
            "GEMINI_API_KEY no configurada. Utilizando FreeWebTranslatorAdapter (traducción online gratuita con caché SQLite)."
        )
        translator = FreeWebTranslatorAdapter()

    translate_use_case = TranslateTokenUseCase(
        translator=translator,
        cache=cache,
        segmenter=segmenter,
    )

    process_doc_use_case = ProcessDocumentUseCase(
        pdf_extractor=pdf_extractor,
        ocr_engine=ocr_engine,
        translate_use_case=translate_use_case,
    )

    logger.info("Instancias de Casos de Uso y Adaptadores creadas exitosamente.")
    return DesktopFacade(
        process_document_use_case=process_doc_use_case,
        translate_token_use_case=translate_use_case,
        segmenter=segmenter,
    )


def main():
    setup_logger()
    logger.info("==========================================================")
    logger.info("🚀 Iniciando Moon Shang - Traductor Chino de Escritorio")
    logger.info("==========================================================")

    parser = argparse.ArgumentParser(description="Moon Shang - Traductor Chino de Escritorio")
    parser.add_argument("--dev", action="store_true", help="Ejecutar en modo desarrollo con Vite")
    parser.add_argument("--url", type=str, default="http://localhost:5173", help="URL de desarrollo")
    args = parser.parse_args()

    try:
        _patch_pywebview_qt()
        facade = create_facade()
        target_url = get_frontend_url(is_dev=args.dev, dev_url=args.url)

        logger.info("Creando ventana nativa PyWebView (1280x850)...")
        window = webview.create_window(
            title="Moon Shang - Traductor Chino",
            url=target_url,
            js_api=facade,
            width=1280,
            height=850,
            min_size=(900, 600),
            background_color="#0f172a",
        )
        facade.set_window(window)

        gui_engine = "qt" if sys.platform.startswith("linux") else None
        logger.info("Ventana configurada. Iniciando loop de eventos de PyWebView (gui=%s)...", gui_engine)
        webview.start(debug=args.dev, gui=gui_engine)
        logger.info("Aplicación cerrada de forma ordenada.")
    except Exception:
        logger.exception("Error crítico durante la ejecución de Moon Shang")
        sys.exit(1)


if __name__ == "__main__":
    main()
