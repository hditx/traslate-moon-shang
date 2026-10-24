import os

import httpx

from core.logger import get_logger
from domain.ports import ITranslator

logger = get_logger("translator")


class MockTranslator(ITranslator):
    """Traductor simulado para pruebas y modo sin conexión."""

    def __init__(self, dictionary: dict[str, str] | None = None):
        self.dictionary = dictionary or {
            "你好": "Hola",
            "世界": "Mundo",
            "谢谢": "Gracias",
            "中国": "China",
            "学生": "Estudiante",
            "学习": "Aprender / Estudiar",
        }

    def translate(self, text_zh: str, target_lang: str = "es") -> str:
        text_clean = text_zh.strip()
        if text_clean in self.dictionary:
            return self.dictionary[text_clean]
        return f"[ES] {text_clean}"


class FreeWebTranslatorAdapter(ITranslator):
    """Traductor en línea gratuito con doble motor (Google GTX + MyMemory API) y diccionario local."""

    def __init__(self, dictionary: dict[str, str] | None = None):
        self.dictionary = dictionary or {
            "你好": "Hola",
            "世界": "Mundo",
            "谢谢": "Gracias",
            "中国": "China",
            "学生": "Estudiante",
            "学习": "Aprender / Estudiar",
        }
        self.client = httpx.Client(timeout=8.0)

    def translate(self, text_zh: str, target_lang: str = "es") -> str:
        text_clean = text_zh.strip()
        if not text_clean:
            return ""

        if text_clean in self.dictionary:
            return self.dictionary[text_clean]

        # 1. Motor principal: Google Translate GTX público (rápido y sin límite de cuota)
        try:
            url_gtx = "https://translate.googleapis.com/translate_a/single"
            params_gtx = {
                "client": "gtx",
                "sl": "zh-CN",
                "tl": target_lang,
                "dt": "t",
                "q": text_clean,
            }
            res_gtx = self.client.get(url_gtx, params=params_gtx)
            if res_gtx.status_code == 200:
                data = res_gtx.json()
                if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    translated = "".join([seg[0] for seg in data[0] if seg and seg[0]])
                    if translated.strip():
                        return translated.strip()
        except Exception as e:
            logger.debug("Google Translate GTX no disponible temporalmente: %s", e)

        # 2. Motor secundario: MyMemory API
        try:
            url_mm = "https://api.mymemory.translated.net/get"
            params_mm = {
                "q": text_clean,
                "langpair": f"zh-CN|{target_lang}-{target_lang.upper()}",
            }
            res_mm = self.client.get(url_mm, params=params_mm)
            if res_mm.status_code == 200:
                data = res_mm.json()
                translated = data.get("responseData", {}).get("translatedText")
                if translated and not str(translated).startswith("MYMEMORY WARNING"):
                    return str(translated).strip()
        except Exception as e:
            logger.debug("MyMemory API no disponible temporalmente: %s", e)

        return self.dictionary.get(text_clean, text_clean)



class GeminiTranslatorAdapter(ITranslator):
    """Adaptador de traducción mediante Google Gemini API con respaldo web automático."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        fallback: ITranslator | None = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model
        self.client = httpx.Client(timeout=12.0)
        self.fallback = fallback or FreeWebTranslatorAdapter()

    def translate(self, text_zh: str, target_lang: str = "es") -> str:
        text_clean = text_zh.strip()
        if not text_clean:
            return ""

        if not self.api_key:
            return self.fallback.translate(text_clean, target_lang)

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        prompt = (
            f"Traduce este texto chino al español de manera concisa y natural. "
            f"Devuelve ÚNICAMENTE la traducción, sin explicaciones:\n\n{text_clean}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        try:
            response = self.client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
            logger.warning("Respuesta no exitosa de Gemini API (%d). Recurriendo a respaldo.", response.status_code)
        except Exception as e:
            logger.warning("Fallo al contactar Gemini API (%s). Recurriendo a respaldo.", e)

        return self.fallback.translate(text_clean, target_lang)

