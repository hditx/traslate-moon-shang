from domain.entities import TranslationResult
from domain.ports import ITextSegmenter, ITranslationCache, ITranslator


class TranslateTokenUseCase:
    """Caso de uso para traducir un término chino, gestionando la caché y el Pinyin."""

    def __init__(
        self,
        translator: ITranslator,
        cache: ITranslationCache,
        segmenter: ITextSegmenter,
    ):
        self.translator = translator
        self.cache = cache
        self.segmenter = segmenter

    def execute(self, text_zh: str) -> TranslationResult:
        cleaned_text = text_zh.strip()
        if not cleaned_text:
            return TranslationResult(textZh="", pinyin="", translationEs="", fromCache=False)

        # 1. Comprobar si ya existe en la caché (descartando traducciones dummy simuladas)
        cached = self.cache.get(cleaned_text)
        if cached and not cached.translation_es.startswith("[ES] "):
            return cached

        # 2. Generar Pinyin y Traducir
        pinyin_str = self.segmenter.to_pinyin(cleaned_text)
        translation_es = self.translator.translate(cleaned_text, target_lang="es")

        result = TranslationResult(
            textZh=cleaned_text,
            pinyin=pinyin_str,
            translationEs=translation_es,
            fromCache=False,
        )

        # 3. Guardar en caché para futuras consultas (solo si es traducción válida)
        if not translation_es.startswith("[ES] "):
            self.cache.set(result)
        return result

