import pymupdf

from adapters.cache_sqlite import SqliteTranslationCache
from adapters.ocr_paddle import MockOcrAdapter
from adapters.pdf_pymupdf import PyMuPdfAdapter
from adapters.pinyin_jieba import PinyinJiebaAdapter
from adapters.translator_api import MockTranslator
from domain.entities import BoundingBox, DetectedToken
from use_cases.process_document import ProcessDocumentUseCase
from use_cases.translate_token import TranslateTokenUseCase


def test_translate_token_use_case_caching():
    cache = SqliteTranslationCache(db_path=":memory:")
    segmenter = PinyinJiebaAdapter()
    translator = MockTranslator({"你好": "Hola"})

    use_case = TranslateTokenUseCase(
        translator=translator,
        cache=cache,
        segmenter=segmenter
    )

    # Primera llamada: cache miss
    res1 = use_case.execute("你好")
    assert res1.text_zh == "你好"
    assert res1.pinyin == "nǐ hǎo"
    assert res1.translation_es == "Hola"
    assert res1.from_cache is False

    # Segunda llamada: cache hit
    res2 = use_case.execute("你好")
    assert res2.translation_es == "Hola"
    assert res2.from_cache is True


def test_process_document_use_case_pdf():
    # Crear un PDF de prueba en memoria
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=400)
    page.insert_text((50, 50), "你好", fontname="helv", fontsize=16)
    pdf_bytes = doc.tobytes()
    doc.close()

    cache = SqliteTranslationCache(db_path=":memory:")
    segmenter = PinyinJiebaAdapter()
    translator = MockTranslator({"你好": "Hola"})
    translate_use_case = TranslateTokenUseCase(translator, cache, segmenter)

    # Mock OCR que detecta el token "你好"
    mock_ocr = MockOcrAdapter(
        mock_tokens=[
            DetectedToken(
                id="tok-1",
                textZh="你好",
                pinyin="nǐ hǎo",
                translationEs="",
                box=BoundingBox(x1=50, y1=50, x2=150, y2=80),
                confidence=0.99
            )
        ]
    )

    pdf_extractor = PyMuPdfAdapter()
    process_use_case = ProcessDocumentUseCase(
        pdf_extractor=pdf_extractor,
        ocr_engine=mock_ocr,
        translate_use_case=translate_use_case
    )

    page_data = process_use_case.process_page(
        source=pdf_bytes,
        filename="test.pdf",
        page_number=1,
        auto_translate=True
    )

    assert page_data.page_number == 1
    assert page_data.width > 0
    assert page_data.height > 0
    assert page_data.image_url.startswith("data:image/png;base64,")
    assert len(page_data.tokens) == 1
    assert page_data.tokens[0].text_zh == "你好"
    assert page_data.tokens[0].translation_es == "Hola"
