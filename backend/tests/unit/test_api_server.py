import io
import os
import tempfile
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api_server import create_app


def get_mock_facade():
    mock_facade = MagicMock()
    mock_facade.translate_token.return_value = {
        "textZh": "你好",
        "pinyin": "nǐ hǎo",
        "translationEs": "Hola",
        "fromCache": True,
    }
    mock_facade.get_pinyin.return_value = "jiào"
    mock_facade.process_page.return_value = {
        "pageNumber": 1,
        "width": 800,
        "height": 1200,
        "imageUrl": "data:image/png;base64,mock",
        "tokens": [
          {
            "id": "tok-1",
            "textZh": "你好",
            "pinyin": "nǐ hǎo",
            "translationEs": "Hola",
            "box": {"x1": 10, "y1": 10, "x2": 50, "y2": 30},
            "confidence": 0.99,
          }
        ],
    }
    return mock_facade


def test_health_check_endpoint():
    app = create_app(facade=get_mock_facade())
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "moon_shang_api"
    assert data["mode"] == "online"


def test_translate_token_endpoint():
    mock_facade = get_mock_facade()
    app = create_app(facade=mock_facade)
    client = TestClient(app)

    # 1. Caso exitoso
    response = client.post("/api/translate", json={"textZh": "你好"})
    assert response.status_code == 200
    data = response.json()
    assert data["textZh"] == "你好"
    assert data["translationEs"] == "Hola"
    mock_facade.translate_token.assert_called_once_with("你好")

    # 2. Texto vacío
    empty_res = client.post("/api/translate", json={"textZh": "   "})
    assert empty_res.status_code == 400


def test_get_pinyin_endpoint():
    mock_facade = get_mock_facade()
    app = create_app(facade=mock_facade)
    client = TestClient(app)

    # 1. Caso exitoso
    response = client.get("/api/pinyin", params={"text": "窖"})
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "窖"
    assert data["pinyin"] == "jiào"
    mock_facade.get_pinyin.assert_called_once_with("窖")

    # 2. Texto vacío
    empty_res = client.get("/api/pinyin", params={"text": " "})
    assert empty_res.status_code == 400


def test_get_audio_endpoint():
    app = create_app(facade=get_mock_facade())
    client = TestClient(app)

    # 1. Texto vacío
    res_empty = client.get("/api/audio", params={"text": ""})
    assert res_empty.status_code == 400

    # 2. Con archivo simulado en cache_dir legítimo
    from adapters.tts_audio import GoogleTTSAudioAdapter
    tts_adapter = GoogleTTSAudioAdapter()
    with tempfile.NamedTemporaryFile(dir=tts_adapter.cache_dir, suffix=".mp3", delete=False) as tmp:
        tmp.write(b"MOCK_MP3_DATA")
        tmp_path = tmp.name

    try:
        with patch("adapters.tts_audio.GoogleTTSAudioAdapter.download_audio", return_value=tmp_path):
            res = client.get("/api/audio", params={"text": "你好"})
            assert res.status_code == 200
            assert res.headers["content-type"] == "audio/mpeg"
            assert res.content == b"MOCK_MP3_DATA"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_process_page_endpoint():
    mock_facade = get_mock_facade()
    app = create_app(facade=mock_facade)
    client = TestClient(app)

    # 1. Subida exitosa de imagen PNG
    fake_png = io.BytesIO(b"MOCK_IMAGE_BYTES")
    response = client.post(
        "/api/process-page",
        files={"file": ("page1.png", fake_png, "image/png")},
        data={"page_number": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pageNumber"] == 1
    assert len(data["tokens"]) == 1
    mock_facade.process_page.assert_called_once()

    # 2. Extensión no permitida (.exe)
    fake_exe = io.BytesIO(b"evil")
    res_invalid = client.post(
        "/api/process-page",
        files={"file": ("malicious.exe", fake_exe, "application/octet-stream")},
        data={"page_number": 1},
    )
    assert res_invalid.status_code == 400
    assert "Formato no permitido" in res_invalid.json()["detail"]

    # 3. Número de página inválido (< 1)
    res_page_invalid = client.post(
        "/api/process-page",
        files={"file": ("page1.png", io.BytesIO(b"mock"), "image/png")},
        data={"page_number": 0},
    )
    assert res_page_invalid.status_code == 400
