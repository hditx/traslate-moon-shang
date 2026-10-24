from unittest.mock import MagicMock

import pytest

from adapters.ocr_paddle import MockOcrAdapter, PaddleOcrAdapter
from adapters.pinyin_jieba import PinyinJiebaAdapter


def test_mock_ocr_adapter_returns_tokens():
    adapter = MockOcrAdapter()
    tokens = adapter.detect_text(b"dummy")
    assert len(tokens) == 1
    assert tokens[0].text_zh == "你好世界"
    assert tokens[0].pinyin == "nǐ hǎo shì jiè"
    assert tokens[0].box.width == 200.0


def test_paddle_ocr_invalid_bytes():
    adapter = PaddleOcrAdapter()
    with pytest.raises(ValueError, match="No se pudo decodificar la imagen"):
        adapter.detect_text(b"not-an-image")


def test_paddle_ocr_parses_lines(mocker):
    # Simular imagen válida de 100x100 usando PNG mínimo
    import cv2
    import numpy as np
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, img_bytes = cv2.imencode(".png", img)

    segmenter = PinyinJiebaAdapter()
    adapter = PaddleOcrAdapter(segmenter=segmenter)

    # Mock del método ocr() de Paddle
    mock_ocr_instance = MagicMock()
    mock_ocr_instance.ocr.return_value = [
        [
            [
                [[10.0, 10.0], [90.0, 10.0], [90.0, 40.0], [10.0, 40.0]],
                ("你好", 0.98)
            ]
        ]
    ]
    adapter._ocr = mock_ocr_instance

    tokens = adapter.detect_text(img_bytes.tobytes())
    assert len(tokens) == 1
    token = tokens[0]
    assert token.text_zh == "你好"
    assert token.pinyin == "nǐ hǎo"
    assert token.confidence == 0.98
    assert token.box.x1 == 10.0
    assert token.box.x2 == 90.0
    assert token.box.y1 == 10.0
    assert token.box.y2 == 40.0


def test_paddle_ocr_parses_paddlex_dict_format(mocker):
    import cv2
    import numpy as np
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, img_bytes = cv2.imencode(".png", img)

    segmenter = PinyinJiebaAdapter()
    adapter = PaddleOcrAdapter(segmenter=segmenter)

    mock_ocr_instance = MagicMock()
    mock_ocr_instance.ocr.return_value = [
        {
            "rec_texts": ["谢谢你"],
            "rec_scores": [0.99],
            "rec_polys": [
                [[15.0, 20.0], [85.0, 20.0], [85.0, 50.0], [15.0, 50.0]],
            ],
        }
    ]
    adapter._ocr = mock_ocr_instance

    tokens = adapter.detect_text(img_bytes.tobytes())
    assert len(tokens) == 1
    token = tokens[0]
    assert token.text_zh == "谢谢你"
    assert token.pinyin == "xiè xiè nǐ"
    assert token.confidence == 0.99
    assert token.box.x1 == 15.0
    assert token.box.x2 == 85.0
    assert token.box.y1 == 20.0
    assert token.box.y2 == 50.0

