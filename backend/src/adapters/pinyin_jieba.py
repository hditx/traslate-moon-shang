import jieba
import pypinyin

from domain.ports import ITextSegmenter


class PinyinJiebaAdapter(ITextSegmenter):
    """Adaptador de procesamiento de lenguaje natural en chino usando Jieba y Pypinyin."""

    def segment_words(self, text_zh: str) -> list[str]:
        if not text_zh or not text_zh.strip():
            return []
        tokens = [token.strip() for token in jieba.cut(text_zh, cut_all=False)]
        return [token for token in tokens if token]

    def to_pinyin(self, text_zh: str) -> str:
        if not text_zh or not text_zh.strip():
            return ""
        syllables = pypinyin.lazy_pinyin(
            text_zh,
            style=pypinyin.Style.TONE,
            errors="default"
        )
        return " ".join(syllables)
