import io
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api_server import create_app
from bridge.desktop_facade import DesktopFacade
from domain.entities import BoundingBox, DetectedToken, PageData


@pytest.fixture
def mock_facade():
    facade = MagicMock(spec=DesktopFacade)
    facade.translate_token.return_value = {
        "textZh": "中国",
        "pinyin": "zhōng guó",
        "translationEs": "China",
        "fromCache": True,
    }
    facade.get_pinyin.return_value = "nǐ hǎo"
    facade.process_page.return_value = PageData(
        pageNumber=1,
        width=800,
        height=1200,
        imageUrl="/path/sample.png",
        tokens=[
            DetectedToken(
                id="tok_1",
                textZh="中国",
                pinyin="zhōng guó",
                translationEs="China",
                box=BoundingBox(x1=10.0, y1=20.0, x2=100.0, y2=80.0),
                confidence=0.99,
            )
        ],
    )
    return facade


@pytest.fixture
def client(mock_facade):
    app = create_app(facade=mock_facade)
    return TestClient(app)


def test_api_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "healthy"]
    assert data["mode"] == "online"


def test_api_process_page_valid_image(client, mock_facade):
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    response = client.post(
        "/api/process-page",
        files={"file": ("documento_chino.png", io.BytesIO(png_bytes), "image/png")},
        data={"page_number": 1},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pageNumber"] == 1
    assert len(data["tokens"]) == 1
    assert data["tokens"][0]["textZh"] == "中国"
    mock_facade.process_page.assert_called_once()


def test_api_process_page_path_traversal_sanitization(client, mock_facade):
    # Intentar enviar ../../etc/passwd como nombre de archivo
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    response = client.post(
        "/api/process-page",
        files={"file": ("../../../../etc/passwd.png", io.BytesIO(png_bytes), "image/png")},
        data={"page_number": 1},
    )
    assert response.status_code == 200
    # Comprobar que el archivo procesado no fue el archivo del sistema sino un temporal seguro
    call_args = mock_facade.process_page.call_args[0]
    temp_file_path = call_args[0]
    assert not temp_file_path.startswith("../")
    assert not temp_file_path.startswith("/etc")


def test_api_process_page_rejects_unallowed_extensions(client):
    dangerous_files = ["malware.exe", "script.sh", "webshell.php", "hack.py", "payload.bat"]
    for filename in dangerous_files:
        response = client.post(
            "/api/process-page",
            files={"file": (filename, io.BytesIO(b"malicious payload"), "application/octet-stream")},
            data={"page_number": 1},
        )
        assert response.status_code == 400
        assert "Formato no permitido" in response.json()["detail"]


def test_api_process_page_rejects_invalid_page_number(client):
    png_bytes = b"\x89PNG\r\n\x1a\n"
    response = client.post(
        "/api/process-page",
        files={"file": ("page.png", io.BytesIO(png_bytes), "image/png")},
        data={"page_number": 0},
    )
    assert response.status_code == 400
    assert "mayor o igual a 1" in response.json()["detail"]


def test_api_process_page_rejects_oversized_file(client, monkeypatch):
    # Probar que se rechaza si se supera el límite de subida
    import api_server

    monkeypatch.setattr(api_server, "MAX_UPLOAD_SIZE", 100)  # Límite bajo para test

    oversized_data = b"X" * 150
    response = client.post(
        "/api/process-page",
        files={"file": ("huge.png", io.BytesIO(oversized_data), "image/png")},
        data={"page_number": 1},
    )
    assert response.status_code == 413
    assert "tamaño máximo permitido" in response.json()["detail"]


def test_api_translate_security_validations(client):
    # Texto vacío
    resp_empty = client.post("/api/translate", json={"textZh": "   "})
    assert resp_empty.status_code == 400

    # Texto con caracteres chinos normales
    resp_valid = client.post("/api/translate", json={"textZh": "中国"})
    assert resp_valid.status_code == 200
    assert resp_valid.json()["translationEs"] == "China"

    # Texto que excede longitud máxima (ReDoS / DoS prevention)
    huge_text = "中" * 6000
    resp_oversized = client.post("/api/translate", json={"textZh": huge_text})
    assert resp_oversized.status_code == 422  # Pydantic validation error


def test_api_pinyin_security_validations(client):
    resp_empty = client.get("/api/pinyin?text=")
    assert resp_empty.status_code == 400

    resp_valid = client.get("/api/pinyin?text=你好")
    assert resp_valid.status_code == 200
    assert resp_valid.json()["pinyin"] == "nǐ hǎo"


def test_api_audio_path_traversal_protection(client, monkeypatch):
    from adapters.tts_audio import GoogleTTSAudioAdapter

    # Simular que download_audio retorna una ruta fuera del cache_dir (intento de path traversal)
    monkeypatch.setattr(GoogleTTSAudioAdapter, "download_audio", lambda self, text: "/etc/passwd")

    response = client.get("/api/audio?text=test")
    # Debe ser denegado por la verificación de confinamiento de ruta (403 Forbidden)
    assert response.status_code == 403
    assert "Acceso denegado" in response.json()["detail"]
