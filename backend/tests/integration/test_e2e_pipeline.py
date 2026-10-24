import os
import tempfile

import pymupdf

from adapters.cache_sqlite import SqliteTranslationCache
from adapters.ocr_paddle import MockOcrAdapter
from adapters.pdf_pymupdf import PyMuPdfAdapter
from adapters.pinyin_jieba import PinyinJiebaAdapter
from adapters.translator_api import MockTranslator
from bridge.desktop_facade import DesktopFacade
from domain.entities import BoundingBox, DetectedToken
from use_cases.process_document import ProcessDocumentUseCase
from use_cases.translate_token import TranslateTokenUseCase


def test_full_e2e_desktop_pipeline():
    # 1. Crear documento PDF de prueba
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=500)
    page.insert_text((50, 100), "欢迎使用中文翻译系统", fontname="helv", fontsize=20)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
        doc.save(tmp_path)
    doc.close()

    try:
        # 2. Configurar arquitectura completa
        pdf_extractor = PyMuPdfAdapter()
        segmenter = PinyinJiebaAdapter()
        cache = SqliteTranslationCache(db_path=":memory:")
        translator = MockTranslator({
            "欢迎使用中文翻译系统": "Bienvenido al sistema de traducción de chino",
            "你好": "Hola"
        })

        mock_ocr = MockOcrAdapter(
            mock_tokens=[
                DetectedToken(
                    id="e2e-1",
                    textZh="欢迎使用中文翻译系统",
                    pinyin="huān yíng shǐ yòng zhōng wén fān yì xì tǒng",
                    translationEs="",
                    box=BoundingBox(x1=50, y1=100, x2=350, y2=140),
                    confidence=0.99
                )
            ]
        )

        trans_use_case = TranslateTokenUseCase(translator, cache, segmenter)
        proc_use_case = ProcessDocumentUseCase(pdf_extractor, mock_ocr, trans_use_case)
        facade = DesktopFacade(proc_use_case, trans_use_case)

        # 3. Paso A: Consultar información del documento
        doc_info = facade.get_document_info(tmp_path)
        assert doc_info["fileType"] == "pdf"
        assert doc_info["totalPages"] == 1
        assert doc_info["id"] == os.path.basename(tmp_path)

        # 4. Paso B: Procesar página con extracción y OCR
        page_data = facade.process_page(tmp_path, page_number=1)
        assert page_data["pageNumber"] == 1
        assert page_data["width"] > 0
        assert page_data["imageUrl"].startswith("data:image/png;base64,")
        assert len(page_data["tokens"]) == 1

        token = page_data["tokens"][0]
        assert token["textZh"] == "欢迎使用中文翻译系统"
        assert token["translationEs"] == "Bienvenido al sistema de traducción de chino"
        assert token["pinyin"] == "huān yíng shǐ yòng zhōng wén fān yì xì tǒng"

        # 5. Paso C: Traducción interactiva de término individual
        single_trans = facade.translate_token("你好")
        assert single_trans["textZh"] == "你好"
        assert single_trans["translationEs"] == "Hola"
        assert single_trans["pinyin"] == "nǐ hǎo"

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
