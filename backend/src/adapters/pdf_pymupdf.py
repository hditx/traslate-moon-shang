import pymupdf

from core.logger import get_logger
from domain.ports import IPdfExtractor

logger = get_logger("pdf")


class PyMuPdfAdapter(IPdfExtractor):
    """Adaptador para extracción y renderizado de PDFs usando PyMuPDF con gestión segura de memoria."""

    def _open_document(self, source: str | bytes) -> pymupdf.Document:
        try:
            if isinstance(source, bytes):
                return pymupdf.open(stream=source, filetype="pdf")
            return pymupdf.open(source)
        except Exception:
            logger.exception("Error al abrir documento PDF con PyMuPDF")
            raise

    def get_page_count(self, source: str | bytes) -> int:
        doc = self._open_document(source)
        try:
            count = len(doc)
            logger.debug("PDF abierto con éxito. Total de páginas: %d", count)
            return count
        finally:
            doc.close()

    def extract_page_as_image(
        self, source: str | bytes, page_number: int, dpi: int = 150
    ) -> tuple[bytes, int, int]:
        doc = self._open_document(source)
        try:
            total_pages = len(doc)
            if page_number < 1 or page_number > total_pages:
                logger.error("Página solicitada (%d) fuera de rango (1..%d)", page_number, total_pages)
                raise ValueError(
                    f"Página {page_number} fuera de rango. El documento tiene {total_pages} página(s)."
                )

            logger.debug("Renderizando página %d a imagen (DPI: %d)...", page_number, dpi)
            page = doc.load_page(page_number - 1)
            pix = page.get_pixmap(dpi=dpi)
            image_bytes = pix.tobytes("png")
            width, height = pix.width, pix.height
            logger.debug("Página %d renderizada exitosamente (%dx%d px, %d bytes)", page_number, width, height, len(image_bytes))
            return image_bytes, width, height
        finally:
            doc.close()
