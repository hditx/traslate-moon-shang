import jieba
import pymupdf
import pypinyin

from domain.entities import BoundingBox, DetectedToken


def test_domain_entities_serialization():
    box = BoundingBox(x1=10.0, y1=20.0, x2=110.0, y2=60.0)
    assert box.width == 100.0
    assert box.height == 40.0

    token = DetectedToken(
        id="t-1",
        textZh="你好",
        pinyin="nǐ hǎo",
        translationEs="Hola",
        box=box,
        confidence=0.99
    )
    assert token.text_zh == "你好"
    assert token.pinyin == "nǐ hǎo"

    data = token.model_dump(by_alias=True)
    assert data["textZh"] == "你好"
    assert data["translationEs"] == "Hola"
    assert data["box"]["x1"] == 10.0


def test_pypinyin_integration():
    hanzi = "你好世界"
    pinyin_list = pypinyin.lazy_pinyin(hanzi, style=pypinyin.Style.TONE)
    assert pinyin_list == ["nǐ", "hǎo", "shì", "jiè"]


def test_jieba_segmentation():
    sentence = "我是中国学生"
    words = list(jieba.cut(sentence))
    assert "学生" in words
    assert "我" in words


def test_pymupdf_available():
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=300)
    assert page.rect.width == 300
    doc.close()
