import pymupdf
import pytest

from adapters.pdf_pymupdf import PyMuPdfAdapter


@pytest.fixture
def sample_pdf_bytes():
    """Crea un PDF de 2 páginas en memoria con texto."""
    doc = pymupdf.open()
    # Página 1 (300 x 400 pt)
    page1 = doc.new_page(width=300, height=400)
    page1.insert_text((50, 50), "你好，第一页", fontname="helv", fontsize=16)

    # Página 2 (300 x 400 pt)
    page2 = doc.new_page(width=300, height=400)
    page2.insert_text((50, 50), "第二页内容", fontname="helv", fontsize=16)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_get_page_count(sample_pdf_bytes):
    adapter = PyMuPdfAdapter()
    assert adapter.get_page_count(sample_pdf_bytes) == 2


def test_extract_page_as_image(sample_pdf_bytes):
    adapter = PyMuPdfAdapter()
    # Extraer página 1 con DPI 144 (escala x2 respecto a 72 pt base)
    image_bytes, width, height = adapter.extract_page_as_image(sample_pdf_bytes, page_number=1, dpi=144)

    assert isinstance(image_bytes, bytes)
    assert len(image_bytes) > 0
    # A 144 DPI (72 * 2), un documento de 300x400 pt mide 600x800 px
    assert width == 600
    assert height == 800

    # Verificar que el encabezado del archivo es PNG
    assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n'


def test_invalid_page_number_raises_error(sample_pdf_bytes):
    adapter = PyMuPdfAdapter()
    with pytest.raises(ValueError, match="Página 0 fuera de rango"):
        adapter.extract_page_as_image(sample_pdf_bytes, page_number=0)

    with pytest.raises(ValueError, match="Página 3 fuera de rango"):
        adapter.extract_page_as_image(sample_pdf_bytes, page_number=3)
