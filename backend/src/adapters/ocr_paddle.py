import locale
import os
import uuid

import cv2
import numpy as np

from core.logger import get_logger
from domain.entities import BoundingBox, DetectedToken
from domain.ports import IOCREngine, ITextSegmenter

logger = get_logger("ocr")


# Forzar LC_NUMERIC="C" para evitar que Qt/Protobuf falle al parsear números flotantes con punto
os.environ["LC_NUMERIC"] = "C"
try:
    locale.setlocale(locale.LC_NUMERIC, "C")
except Exception:
    pass

# Prevenir incompatibilidad de OneDNN en CPU con PIR en PaddlePaddle 3.x
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"
# Desactivar inicialización ansiosa de submódulos de entrenamiento innecesarios en PaddleX
os.environ["PADDLE_PDX_EAGER_INIT"] = "False"

# Shim de importlib.metadata para ejecutables congelados con PyInstaller
# PaddleX consulta versiones con importlib.metadata.version(dep), lo que falla en PyInstaller
# si los metadatos .dist-info no están disponibles. Este shim garantiza que siempre devuelva
# una versión válida para las dependencias empaquetadas.
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


_paddlex_patched = False


def _patch_paddlex_for_pyinstaller() -> None:
    """
    Asegura que PaddleX funcione correctamente tanto en desarrollo como dentro del bundle
    congelado de PyInstaller (sys._MEIPASS):
    1. Pre-parchea paddlex.utils.deps (safe is_dep_available, require_deps, require_extra).
    2. Hace idempotente repo_manager.initialize para evitar errores de re-inicialización.
    3. Precarga bibliotecas nativas de Paddle con RTLD_GLOBAL (libiomp5, libmklml_intel).
    4. Resuelve rutas de configuración de pipelines (ej. OCR.yaml).
    5. Inyecta referencias seguras a cv2, pyclipper y shapely en los procesadores de detección/corte.
    """
    global _paddlex_patched
    if _paddlex_patched:
        return
    _paddlex_patched = True

    import importlib.util
    import sys
    from pathlib import Path

    # 1. Pre-parchear paddlex.utils.deps ANTES de importar pipelines
    try:
        import paddlex.utils.deps as px_deps

        spec_map = {
            "opencv-contrib-python": "cv2",
            "opencv-python": "cv2",
            "paddlepaddle": "paddle",
        }

        def safe_is_dep_available(dep: str, /, check_version: bool = False) -> bool:
            target = spec_map.get(dep, dep.replace("-", "_"))
            try:
                return importlib.util.find_spec(target) is not None
            except Exception:
                return False

        px_deps.is_dep_available = safe_is_dep_available
        px_deps.require_deps = lambda *args, **kwargs: None
        px_deps.is_extra_available = lambda extra: extra.lower() == "ocr"
        px_deps.require_extra = lambda *args, **kwargs: None
        px_deps.get_dep_version = lambda dep: _known_versions.get(dep, "1.0.0")
        logger.debug("Bypass seguro de dependencias en paddlex.utils.deps aplicado correctamente.")
    except Exception as e:
        logger.debug("No se pudo pre-parchear paddlex.utils.deps: %s", e)

    # 1b. Hacer idempotente repo_manager.initialize para prevenir 'PDX has already been initialized'
    try:
        import paddlex.repo_manager.core as repo_core
        orig_init = repo_core.initialize

        def idempotent_repo_init(*args, **kwargs):
            if repo_core._GlobalContext.is_initialized():
                return
            try:
                return orig_init(*args, **kwargs)
            except RuntimeError as err:
                if "already been initialized" in str(err):
                    return
                raise

        repo_core.initialize = idempotent_repo_init
        import paddlex.repo_manager as repo_mgr
        repo_mgr.initialize = idempotent_repo_init
        logger.debug("repo_manager.initialize configurado como idempotente.")
    except Exception as e:
        logger.debug("No se pudo configurar repo_manager como idempotente: %s", e)

    # 2. Pre-cargar bibliotecas dinámicas compartidas de Paddle (libiomp5.so, libmklml_intel.so)
    # En Linux PyInstaller, dlopen("libmklml_intel.so") falla si no está precargada con RTLD_GLOBAL
    try:
        import ctypes
        search_dirs = []
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            search_dirs.extend([
                Path(sys._MEIPASS),
                Path(sys._MEIPASS) / "paddle" / "libs",
            ])
        try:
            import paddle
            search_dirs.append(Path(paddle.__file__).parent / "libs")
        except Exception:
            pass

        for sd in search_dirs:
            if not sd.exists():
                continue
            iomp5_path = sd / "libiomp5.so"
            mklml_path = sd / "libmklml_intel.so"
            if iomp5_path.exists() and mklml_path.exists():
                try:
                    ctypes.CDLL(str(iomp5_path), mode=ctypes.RTLD_GLOBAL)
                    ctypes.CDLL(str(mklml_path), mode=ctypes.RTLD_GLOBAL)
                    logger.debug("Bibliotecas nativas iomp5 y mklml_intel precargadas desde: %s", sd)
                    break
                except Exception as err:
                    logger.debug("Fallo precargando desde %s: %s", sd, err)
    except Exception as e:
        logger.warning("No se pudo precargar bibliotecas nativas de Paddle: %s", e)

    # 3. Parche de rutas de configuración de pipelines (ej. OCR.yaml)
    try:
        import paddlex.inference.pipelines as px_pipelines
        import paddlex.inference.utils.get_pipeline_path as px_utils_path

        def patched_get_pipeline_path(pipeline_name: str) -> str | None:
            # 1. Buscar en el directorio extraído por PyInstaller (_internal / sys._MEIPASS)
            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                candidates = [
                    Path(sys._MEIPASS) / "paddlex" / "configs" / "pipelines" / f"{pipeline_name}.yaml",
                    Path(sys._MEIPASS) / "configs" / "pipelines" / f"{pipeline_name}.yaml",
                ]
                for c in candidates:
                    if c.exists():
                        return str(c)
            # 2. Buscar en la ubicación instalada de paddlex
            try:
                import paddlex
                paddlex_dir = Path(paddlex.__file__).parent
                c = paddlex_dir / "configs" / "pipelines" / f"{pipeline_name}.yaml"
                if c.exists():
                    return str(c)
            except Exception:
                pass
            # 3. Fallback a la resolución relativa por defecto
            try:
                c = (
                    Path(px_pipelines.__file__).parent.parent.parent
                    / "configs/pipelines"
                    / f"{pipeline_name}.yaml"
                ).resolve()
                if c.exists():
                    return str(c)
            except Exception:
                pass
            return None

        px_pipelines.get_pipeline_path = patched_get_pipeline_path
        px_utils_path.get_pipeline_path = patched_get_pipeline_path
        logger.debug("Parche de rutas de configuración PaddleX para PyInstaller aplicado correctamente.")
    except Exception as e:
        logger.warning("No se pudo aplicar el parche de rutas PaddleX: %s", e)

    # 4. Asegurar inyección explícita de cv2, pyclipper y shapely en procesadores de PaddleX
    try:
        import cv2
        import pyclipper
        import shapely
        from shapely.geometry import Polygon

        # Inyectar en text_detection.processors (evita NameError: name 'pyclipper' is not defined)
        try:
            import paddlex.inference.models.text_detection.processors as det_proc
            det_proc.cv2 = cv2
            det_proc.pyclipper = pyclipper
        except Exception:
            pass

        # Inyectar en crop_image_regions (evita NameError: name 'Polygon' is not defined)
        try:
            import paddlex.inference.pipelines.components.common.crop_image_regions as crop_regions
            crop_regions.cv2 = cv2
            crop_regions.shapely = shapely
            crop_regions.Polygon = Polygon
        except Exception:
            pass

        # Inyectar en image_reader
        try:
            import paddlex.inference.common.reader.image_reader as img_reader
            img_reader.cv2 = cv2
        except Exception:
            pass

        # Barrido preventivo para cualquier otro módulo paddlex en sys.modules
        for mod_name, mod in list(sys.modules.items()):
            if mod is not None and mod_name.startswith("paddlex"):
                if not hasattr(mod, "cv2"):
                    try:
                        setattr(mod, "cv2", cv2)
                    except Exception:
                        pass
                if not hasattr(mod, "pyclipper"):
                    try:
                        setattr(mod, "pyclipper", pyclipper)
                    except Exception:
                        pass
                if not hasattr(mod, "Polygon"):
                    try:
                        setattr(mod, "Polygon", Polygon)
                    except Exception:
                        pass
                if not hasattr(mod, "shapely"):
                    try:
                        setattr(mod, "shapely", shapely)
                    except Exception:
                        pass
        logger.debug("Inyección de dependencias binarias (cv2, pyclipper, shapely) en PaddleX completada.")
    except Exception as e:
        logger.debug("No se pudo inyectar dependencias binarias en submódulos de PaddleX: %s", e)


# Aplicar el parche preventivo tempranamente al importar el módulo
_patch_paddlex_for_pyinstaller()


class MockOcrAdapter(IOCREngine):
    """Adaptador de OCR simulado para tests unitarios rápidos y desarrollo sin GPU."""

    def __init__(self, mock_tokens: list[DetectedToken] | None = None):
        self.mock_tokens = mock_tokens or []

    def detect_text(self, image_bytes: bytes) -> list[DetectedToken]:
        if self.mock_tokens:
            return self.mock_tokens
        # Token simulado por defecto
        return [
            DetectedToken(
                id="mock-1",
                textZh="你好世界",
                pinyin="nǐ hǎo shì jiè",
                translationEs="Hola mundo",
                box=BoundingBox(x1=50.0, y1=50.0, x2=250.0, y2=100.0),
                confidence=0.99,
            )
        ]


class PaddleOcrAdapter(IOCREngine):
    """Adaptador de OCR usando el modelo PaddleOCR en chino compatible con v2 y v3."""

    def __init__(
        self,
        segmenter: ITextSegmenter | None = None,
        use_angle_cls: bool = True,
        lang: str = "ch",
    ):
        self.segmenter = segmenter
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self._ocr = None  # Carga perezosa (lazy-load) para no retrasar el inicio de la app

    def _get_ocr(self):
        if self._ocr is None:
            logger.info("Cargando modelo PaddleOCR (lang=%s, use_angle_cls=%s)...", self.lang, self.use_angle_cls)
            try:
                # Restaurar LC_NUMERIC a "C" para prevenir que Qt/QApplication en locales como es_ES.UTF-8
                # rompa el descriptor pool de Google Protobuf al leer defaults tipo 0.8
                os.environ["LC_NUMERIC"] = "C"
                try:
                    locale.setlocale(locale.LC_NUMERIC, "C")
                except Exception:
                    pass

                # Prevenir incompatibilidad de OneDNN en CPU con PIR en PaddlePaddle 3.x
                os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"
                _patch_paddlex_for_pyinstaller()
                from paddleocr import PaddleOCR
                try:
                    self._ocr = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang)
                except TypeError:
                    self._ocr = PaddleOCR(lang=self.lang)
                logger.info("Modelo PaddleOCR cargado exitosamente.")
            except Exception:
                logger.exception("Fallo al inicializar el modelo PaddleOCR")
                raise
        return self._ocr

    def detect_text(self, image_bytes: bytes) -> list[DetectedToken]:
        logger.debug("Iniciando detección OCR para imagen (%d bytes)...", len(image_bytes))
        # Decodificar bytes a formato imagen BGR para OpenCV/Paddle
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            logger.error("No se pudo decodificar la imagen: buffer de bytes corrupto o inválido.")
            raise ValueError("No se pudo decodificar la imagen a partir de los bytes provistos.")

        ocr = self._get_ocr()
        try:
            results = ocr.ocr(img)
        except Exception:
            logger.exception("Error durante la ejecución del OCR en la imagen")
            raise

        detected_tokens: list[DetectedToken] = []

        if not results or not results[0]:
            return detected_tokens

        # Formato PaddleOCR v3 / PaddleX (diccionario con rec_texts, rec_scores, rec_polys / dt_polys)
        if isinstance(results[0], dict):
            res_dict = results[0]
            texts = res_dict.get("rec_texts", [])
            scores = res_dict.get("rec_scores", [])
            polys = res_dict.get("rec_polys", res_dict.get("dt_polys", []))

            for i, text in enumerate(texts):
                text_str = str(text).strip()
                if not text_str:
                    continue

                conf = float(scores[i]) if i < len(scores) else 1.0
                pts = polys[i] if i < len(polys) else []

                if len(pts) >= 4:
                    x_coords = [float(p[0]) for p in pts]
                    y_coords = [float(p[1]) for p in pts]
                    box = BoundingBox(
                        x1=min(x_coords),
                        y1=min(y_coords),
                        x2=max(x_coords),
                        y2=max(y_coords),
                    )
                else:
                    box = BoundingBox(x1=0.0, y1=0.0, x2=100.0, y2=100.0)

                pinyin_str = self.segmenter.to_pinyin(text_str) if self.segmenter else ""

                detected_tokens.append(
                    DetectedToken(
                        id=str(uuid.uuid4())[:8],
                        textZh=text_str,
                        pinyin=pinyin_str,
                        translationEs="",
                        box=box,
                        confidence=conf,
                    )
                )

            logger.info("OCR completado (formato PaddleX): %d tokens detectados", len(detected_tokens))
            return detected_tokens

        # Formato PaddleOCR v2 / Legacy (lista de tuplas [points, (text, conf)])
        for line in results[0]:
            points, (text, conf) = line
            text_str = str(text).strip()
            if not text_str:
                continue

            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]

            box = BoundingBox(
                x1=float(min(x_coords)),
                y1=float(min(y_coords)),
                x2=float(max(x_coords)),
                y2=float(max(y_coords)),
            )

            pinyin_str = self.segmenter.to_pinyin(text_str) if self.segmenter else ""

            detected_tokens.append(
                DetectedToken(
                    id=str(uuid.uuid4())[:8],
                    textZh=text_str,
                    pinyin=pinyin_str,
                    translationEs="",
                    box=box,
                    confidence=float(conf),
                )
            )

        logger.info("OCR completado (formato Legacy): %d tokens detectados", len(detected_tokens))
        return detected_tokens
