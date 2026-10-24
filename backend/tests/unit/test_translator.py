from unittest.mock import MagicMock

from adapters.translator_api import (
    FreeWebTranslatorAdapter,
    GeminiTranslatorAdapter,
    MockTranslator,
)



def test_mock_translator_known_words():
    translator = MockTranslator({"你好": "Hola", "世界": "Mundo"})
    assert translator.translate("你好") == "Hola"
    assert translator.translate("世界") == "Mundo"


def test_mock_translator_fallback():
    translator = MockTranslator()
    # Para palabras no registradas en el mock, retorna una traducción simulada
    result = translator.translate("未知词汇")
    assert "[ES] 未知词汇" in result


def test_free_web_translator_adapter_local_dict():
    translator = FreeWebTranslatorAdapter({"你好": "Hola"})
    assert translator.translate("你好") == "Hola"
    assert translator.translate("") == ""


def test_free_web_translator_adapter_api_mock(monkeypatch):
    translator = FreeWebTranslatorAdapter()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "responseData": {"translatedText": "Si alguien le dice a la marioneta"}
    }
    monkeypatch.setattr(translator.client, "get", lambda url, params: mock_resp)

    res = translator.translate("如果别人跟小木偶说")
    assert res == "Si alguien le dice a la marioneta"


def test_gemini_translator_initialization():
    translator = GeminiTranslatorAdapter(api_key="test-key")
    assert translator.api_key == "test-key"
    assert translator.model == "gemini-2.5-flash"
    assert isinstance(translator.fallback, FreeWebTranslatorAdapter)
