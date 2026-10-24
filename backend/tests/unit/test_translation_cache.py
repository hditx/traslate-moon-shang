from adapters.cache_sqlite import SqliteTranslationCache
from domain.entities import TranslationResult


def test_cache_miss_returns_none():
    cache = SqliteTranslationCache(db_path=":memory:")
    assert cache.get("你好") is None


def test_cache_set_and_get():
    cache = SqliteTranslationCache(db_path=":memory:")
    item = TranslationResult(
        textZh="谢谢",
        pinyin="xiè xie",
        translationEs="Gracias",
        fromCache=False
    )
    cache.set(item)

    cached = cache.get("谢谢")
    assert cached is not None
    assert cached.text_zh == "谢谢"
    assert cached.pinyin == "xiè xie"
    assert cached.translation_es == "Gracias"
    assert cached.from_cache is True


def test_cache_overwrite():
    cache = SqliteTranslationCache(db_path=":memory:")
    item1 = TranslationResult(textZh="水", pinyin="shuǐ", translationEs="Agua")
    item2 = TranslationResult(textZh="水", pinyin="shuǐ", translationEs="Agua (líquido)")

    cache.set(item1)
    cache.set(item2)

    cached = cache.get("水")
    assert cached is not None
    assert cached.translation_es == "Agua (líquido)"
