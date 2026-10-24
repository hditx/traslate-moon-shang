import os
import tempfile
from unittest.mock import MagicMock

import pytest

from bridge.desktop_facade import DesktopFacade
from domain.entities import BoundingBox, DetectedToken, DocumentData, PageData, TranslationResult


def test_desktop_facade_get_document_info():
    mock_doc_use_case = MagicMock()
    mock_trans_use_case = MagicMock()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4 mock")
        tmp_path = tmp.name

    try:
        mock_doc_use_case.get_document_info.return_value = DocumentData(
            id="sample.pdf",
            filename=os.path.basename(tmp_path),
            fileType="pdf",
            totalPages=3,
            currentPage=1,
            pages=[],
        )

        facade = DesktopFacade(
            process_document_use_case=mock_doc_use_case,
            translate_token_use_case=mock_trans_use_case,
        )

        info = facade.get_document_info(tmp_path)
        assert info["filename"] == os.path.basename(tmp_path)
        assert info["fileType"] == "pdf"
        assert info["totalPages"] == 3
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_desktop_facade_process_page():
    mock_doc_use_case = MagicMock()
    mock_trans_use_case = MagicMock()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(b"mockpng")
        tmp_path = tmp.name

    try:
        mock_doc_use_case.process_page.return_value = PageData(
            pageNumber=1,
            width=800,
            height=1200,
            imageUrl="data:image/png;base64,mock",
            tokens=[
                DetectedToken(
                    id="tok-1",
                    textZh="你好",
                    pinyin="nǐ hǎo",
                    translationEs="Hola",
                    box=BoundingBox(x1=10, y1=10, x2=50, y2=30),
                    confidence=0.99,
                )
            ],
        )

        facade = DesktopFacade(
            process_document_use_case=mock_doc_use_case,
            translate_token_use_case=mock_trans_use_case,
        )

        page = facade.process_page(tmp_path, 1)
        assert page["pageNumber"] == 1
        assert page["width"] == 800
        assert len(page["tokens"]) == 1
        assert page["tokens"][0]["textZh"] == "你好"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_desktop_facade_translate_token():
    mock_doc_use_case = MagicMock()
    mock_trans_use_case = MagicMock()

    mock_trans_use_case.execute.return_value = TranslationResult(
        textZh="谢谢",
        pinyin="xiè xie",
        translationEs="Gracias",
        fromCache=True,
    )

    facade = DesktopFacade(
        process_document_use_case=mock_doc_use_case,
        translate_token_use_case=mock_trans_use_case,
    )

    result = facade.translate_token("谢谢")
    assert result["textZh"] == "谢谢"
    assert result["translationEs"] == "Gracias"
    assert result["fromCache"] is True


def test_desktop_facade_security_path_traversal_and_extensions():
    facade = DesktopFacade(
        process_document_use_case=MagicMock(),
        translate_token_use_case=MagicMock(),
    )

    # 1. Ruta vacía
    with pytest.raises(ValueError, match="La ruta del archivo no puede estar vacía"):
        facade.get_document_info("")

    # 2. Archivo inexistente
    with pytest.raises(FileNotFoundError, match="El archivo especificado no existe"):
        facade.get_document_info("/tmp/archivo_fantasma_inexistente_12345.pdf")

    # 3. Extensión no permitida (ej. .exe, .sh)
    with tempfile.NamedTemporaryFile(suffix=".sh", delete=False) as tmp:
        tmp.write(b"echo evil")
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="Tipo de archivo no permitido"):
            facade.get_document_info(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_desktop_facade_copy_to_clipboard(monkeypatch):
    facade = DesktopFacade(
        process_document_use_case=MagicMock(),
        translate_token_use_case=MagicMock(),
    )

    # Caso 1: Sin QApplication instance
    assert facade.copy_to_clipboard("Texto prueba") in (True, False)

    # Caso 2: Con mock de QApplication
    mock_app = MagicMock()
    mock_clipboard = MagicMock()
    mock_app.clipboard.return_value = mock_clipboard
    monkeypatch.setattr("PyQt6.QtWidgets.QApplication.instance", lambda: mock_app)

    res = facade.copy_to_clipboard("Hola Mundo")
    assert res is True
    mock_clipboard.setText.assert_called_once_with("Hola Mundo")


def test_desktop_facade_get_pinyin():
    mock_segmenter = MagicMock()
    mock_segmenter.to_pinyin.return_value = "jiào"

    facade = DesktopFacade(
        process_document_use_case=MagicMock(),
        translate_token_use_case=MagicMock(),
        segmenter=mock_segmenter,
    )

    # Texto válido con segmenter inyectado
    assert facade.get_pinyin("窖") == "jiào"
    mock_segmenter.to_pinyin.assert_called_once_with("窖")

    # Texto vacío
    assert facade.get_pinyin("") == ""
    assert facade.get_pinyin("   ") == ""


def test_desktop_facade_play_pronunciation():
    mock_tts = MagicMock()
    mock_tts.play_pronunciation.return_value = True

    facade = DesktopFacade(
        process_document_use_case=MagicMock(),
        translate_token_use_case=MagicMock(),
        tts_player=mock_tts,
    )

    # Texto válido
    assert facade.play_pronunciation("你好") is True
    mock_tts.play_pronunciation.assert_called_once_with("你好")

    # Texto vacío
    assert facade.play_pronunciation("") is False
    assert facade.play_pronunciation("   ") is False

