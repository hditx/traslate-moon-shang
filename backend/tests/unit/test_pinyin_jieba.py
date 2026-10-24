from adapters.pinyin_jieba import PinyinJiebaAdapter


def test_segment_words():
    adapter = PinyinJiebaAdapter()
    words = adapter.segment_words("我是中国学生")
    assert "我" in words
    assert "学生" in words
    assert "是" in words


def test_to_pinyin_with_tones():
    adapter = PinyinJiebaAdapter()
    pinyin = adapter.to_pinyin("你好世界")
    assert pinyin == "nǐ hǎo shì jiè"


def test_to_pinyin_with_mixed_content():
    adapter = PinyinJiebaAdapter()
    pinyin = adapter.to_pinyin("你好 123")
    assert "nǐ hǎo" in pinyin
    assert "123" in pinyin


def test_empty_string_handling():
    adapter = PinyinJiebaAdapter()
    assert adapter.segment_words("") == []
    assert adapter.to_pinyin("") == ""
