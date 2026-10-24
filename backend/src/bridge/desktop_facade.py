import os
import time

from core.logger import get_logger
from domain.ports import ITextSegmenter, ITextToSpeech
from use_cases.process_document import ProcessDocumentUseCase
from use_cases.translate_token import TranslateTokenUseCase

logger = get_logger("facade")

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


class DesktopFacade:
    """Fachada que expone métodos de negocio a la ventana de escritorio PyWebView con validación de seguridad y logs."""

    def __init__(
        self,
        process_document_use_case: ProcessDocumentUseCase,
        translate_token_use_case: TranslateTokenUseCase,
        window=None,
        tts_player: ITextToSpeech | None = None,
        segmenter: ITextSegmenter | None = None,
    ):
        self.doc_use_case = process_document_use_case
        self.trans_use_case = translate_token_use_case
        self.window = window
        self._active_file_path: str | None = None
        self.segmenter = segmenter or getattr(translate_token_use_case, "segmenter", None)
        self.tts_player = tts_player

    def set_window(self, window):
        self.window = window

    def _validate_file_path(self, file_path: str) -> str:
        """Valida que la ruta sea segura, exista y tenga una extensión permitida (prevención de path traversal)."""
        if not file_path or not isinstance(file_path, str) or not file_path.strip():
            logger.error("Ruta de archivo vacía o inválida recibida: %r", file_path)
            raise ValueError("La ruta del archivo no puede estar vacía.")

        # Si se pasa solo el nombre base o identificador del archivo activo actual, reutilizar la ruta absoluta
        raw_clean = file_path.strip()
        if self._active_file_path and (
            raw_clean == self._active_file_path
            or raw_clean == os.path.basename(self._active_file_path)
        ):
            return self._active_file_path

        # Resolver ruta canónica absoluta eliminando componentes relativos '../'
        normalized_path = os.path.realpath(os.path.abspath(os.path.expanduser(raw_clean)))

        if not os.path.exists(normalized_path):
            # Verificación de respaldo contra el archivo activo
            if self._active_file_path and os.path.basename(self._active_file_path) == os.path.basename(normalized_path):
                return self._active_file_path
            logger.error("Archivo no encontrado en el sistema: %s", normalized_path)
            raise FileNotFoundError(f"El archivo especificado no existe: {file_path}")

        if not os.path.isfile(normalized_path):
            logger.error("La ruta no es un archivo regular: %s", normalized_path)
            raise ValueError(f"La ruta especificada no es un archivo regular: {file_path}")

        _, ext = os.path.splitext(normalized_path)
        if ext.lower() not in ALLOWED_EXTENSIONS:
            logger.error("Extensión no permitida (%s) para el archivo: %s", ext, normalized_path)
            raise ValueError(
                f"Tipo de archivo no permitido: '{ext}'. Formatos soportados: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        return normalized_path

    def open_file_dialog(self) -> dict | None:
        """Abre el diálogo nativo de selección de archivos del sistema operativo."""
        logger.info("Abriendo diálogo nativo de selección de archivo...")
        if not self.window:
            try:
                import webview
                if hasattr(webview, "windows") and webview.windows:
                    self.window = webview.windows[0]
            except (ImportError, AttributeError):
                self.window = None

        if not self.window:
            logger.warning("No se encontró ventana activa para abrir el diálogo de archivo.")
            return None

        import webview
        file_types = (
            "Archivos compatibles (*.pdf;*.png;*.jpg;*.jpeg;*.webp)",
            "Todos los archivos (*.*)",
        )

        dialog_type = (
            webview.FileDialog.OPEN
            if hasattr(webview, "FileDialog") and hasattr(webview.FileDialog, "OPEN")
            else getattr(webview, "OPEN_DIALOG", 0)
        )

        try:
            result = self.window.create_file_dialog(
                dialog_type,
                allow_multiple=False,
                file_types=file_types,
            )

            if result and len(result) > 0:
                selected_path = self._validate_file_path(result[0])
                self._active_file_path = selected_path
                filename = os.path.basename(selected_path)
                logger.info("Archivo seleccionado por el usuario: %s (Nombre: %s)", selected_path, filename)
                return {
                    "filePath": selected_path,
                    "filename": filename,
                }

            logger.info("El usuario canceló la selección de archivo.")
            return None
        except Exception:
            logger.exception("Error al invocar diálogo de archivos")
            raise

    def get_document_info(self, file_path: str) -> dict:
        """Obtiene la información general del archivo cargado de forma segura."""
        t0 = time.perf_counter()
        logger.info("Solicitud get_document_info para: %s", file_path)
        try:
            safe_path = self._validate_file_path(file_path)
            self._active_file_path = safe_path
            filename = os.path.basename(safe_path)
            doc_info = self.doc_use_case.get_document_info(source=safe_path, filename=safe_path)
            elapsed = time.perf_counter() - t0
            logger.info(
                "get_document_info completado en %.3fs para %s (%d páginas)",
                elapsed,
                filename,
                doc_info.total_pages,
            )
            return doc_info.model_dump(by_alias=True)
        except Exception:
            logger.exception("Fallo al obtener información del documento '%s'", file_path)
            raise

    def process_page(self, file_path: str, page_number: int) -> dict:
        """Procesa una página con OCR y traducción pre-cargada con métricas de tiempo."""
        t0 = time.perf_counter()
        logger.info("Iniciando procesamiento de página %d para archivo: %s", page_number, file_path)
        try:
            safe_path = self._validate_file_path(file_path)
            self._active_file_path = safe_path
            filename = os.path.basename(safe_path)
            page_data = self.doc_use_case.process_page(
                source=safe_path,
                filename=filename,
                page_number=page_number,
                auto_translate=True,
            )
            elapsed = time.perf_counter() - t0
            logger.info(
                "Página %d procesada con éxito en %.3fs (%d tokens detectados)",
                page_number,
                elapsed,
                len(page_data.tokens),
            )
            return page_data.model_dump(by_alias=True)
        except Exception:
            logger.exception("Error procesando página %d del archivo '%s'", page_number, file_path)
            raise

    def translate_token(self, text_zh: str) -> dict:
        """Traduce un carácter o término chino específico."""
        t0 = time.perf_counter()
        logger.debug("Solicitud de traducción para token: '%s'", text_zh)
        try:
            res = self.trans_use_case.execute(text_zh)
            elapsed = time.perf_counter() - t0
            logger.debug(
                "Traducción obtenida para '%s' -> '%s' (Pinyin: '%s') en %.3fs",
                text_zh,
                res.translation_es,
                res.pinyin,
                elapsed,
            )
            return res.model_dump(by_alias=True)
        except Exception:
            logger.exception("Error traduciendo token '%s'", text_zh)
            raise

    def copy_to_clipboard(self, text: str) -> bool:
        """Copia texto al portapapeles del sistema operativo de manera nativa y segura."""
        try:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if app:
                clipboard = app.clipboard()
                clipboard.setText(text)
                logger.debug("Texto copiado al portapapeles nativo Qt (%d caracteres)", len(text))
                return True
            logger.warning("No se encontró instancia de QApplication para copiar al portapapeles")
            return False
        except Exception:
            logger.exception("Error al copiar texto al portapapeles nativo")
            return False

    def get_pinyin(self, text_zh: str) -> str:
        """Convierte texto o carácter chino a su transcripción Pinyin con tonos."""
        if not text_zh or not isinstance(text_zh, str) or not text_zh.strip():
            return ""
        cleaned = text_zh.strip()
        if self.segmenter:
            try:
                return self.segmenter.to_pinyin(cleaned)
            except Exception:
                logger.exception("Error al convertir texto a Pinyin con segmenter para '%s'", cleaned)
        try:
            import pypinyin
            syllables = pypinyin.lazy_pinyin(cleaned, style=pypinyin.Style.TONE)
            return " ".join(syllables)
        except Exception:
            logger.exception("Error en fallback de Pypinyin para '%s'", cleaned)
            return ""

    def play_pronunciation(self, text_zh: str) -> bool:
        """Reproduce la pronunciación auditiva de un término o carácter chino."""
        if not text_zh or not isinstance(text_zh, str) or not text_zh.strip():
            logger.warning("Solicitud de pronunciación con texto vacío")
            return False
        cleaned = text_zh.strip()
        logger.info("Solicitud de reproducción de audio para: '%s'", cleaned)
        try:
            if not self.tts_player:
                from adapters.tts_audio import GoogleTTSAudioAdapter
                self.tts_player = GoogleTTSAudioAdapter()
            return self.tts_player.play_pronunciation(cleaned)
        except Exception:
            logger.exception("Error al reproducir pronunciación para '%s'", cleaned)
            return False


