from abc import ABC, abstractmethod

from domain.entities import DetectedToken, TranslationResult


class IOCREngine(ABC):
    """Puerto para el motor de reconocimiento óptico de caracteres (OCR)."""

    @abstractmethod
    def detect_text(self, image_bytes: bytes) -> list[DetectedToken]:
        """Detecta texto y coordenadas en una imagen en memoria."""


class IPdfExtractor(ABC):
    """Puerto para la extracción de páginas de documentos PDF."""

    @abstractmethod
    def get_page_count(self, source: str | bytes) -> int:
        """Retorna el número total de páginas del PDF."""

    @abstractmethod
    def extract_page_as_image(
        self, source: str | bytes, page_number: int, dpi: int = 150
    ) -> tuple[bytes, int, int]:
        """
        Renderiza la página indicada a una imagen PNG en bytes.
        Retorna (image_bytes, width, height).
        """


class ITextSegmenter(ABC):
    """Puerto para la segmentación de texto chino y conversión a Pinyin."""

    @abstractmethod
    def segment_words(self, text_zh: str) -> list[str]:
        """Segmenta una oración o bloque chino en palabras individuales con sentido."""

    @abstractmethod
    def to_pinyin(self, text_zh: str) -> str:
        """Convierte texto chino a su transcripción fonética con tonos."""


class ITranslator(ABC):
    """Puerto para el servicio de traducción (Strategy Pattern)."""

    @abstractmethod
    def translate(self, text_zh: str, target_lang: str = "es") -> str:
        """Traduce texto en chino al idioma destino (por defecto español)."""


class ITranslationCache(ABC):
    """Puerto para el almacenamiento y caché de traducciones."""

    @abstractmethod
    def get(self, text_zh: str) -> TranslationResult | None:
        """Recupera una traducción previamente guardada si existe."""

    @abstractmethod
    def set(self, result: TranslationResult) -> None:
        """Almacena una traducción en la caché."""

class ITextToSpeech(ABC):
    """Puerto para la síntesis y reproducción de audio/pronunciación."""

    @abstractmethod
    def play_pronunciation(self, text_zh: str) -> bool:
        """Reproduce la pronunciación del texto chino en el sistema."""
