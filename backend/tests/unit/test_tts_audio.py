import os
import tempfile
from unittest.mock import MagicMock, patch

from adapters.tts_audio import GoogleTTSAudioAdapter


def test_google_tts_audio_download_and_cache():
    with tempfile.TemporaryDirectory() as tmp_dir:
        adapter = GoogleTTSAudioAdapter(cache_dir=tmp_dir)

        # Simular descarga HTTP exitosa de Google TTS
        mock_response = MagicMock()
        mock_response.read.return_value = b"MOCK_MP3_AUDIO_BYTES_12345"
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response):
            path = adapter.download_audio("你好")
            assert path is not None
            assert os.path.exists(path)
            with open(path, "rb") as f:
                assert f.read() == b"MOCK_MP3_AUDIO_BYTES_12345"

            # Segunda llamada debe leer desde caché sin llamar a urlopen
            with patch("urllib.request.urlopen") as mock_url_fail:
                cached_path = adapter.download_audio("你好")
                assert cached_path == path
                mock_url_fail.assert_not_called()


def test_google_tts_audio_play_pronunciation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        adapter = GoogleTTSAudioAdapter(cache_dir=tmp_dir)

        # Texto vacío debe retornar False
        assert adapter.play_pronunciation("") is False
        assert adapter.play_pronunciation("   ") is False

        # Con audio simulado y reproductor del sistema
        with patch.object(adapter, "download_audio", return_value=os.path.join(tmp_dir, "test.mp3")):
            with open(os.path.join(tmp_dir, "test.mp3"), "wb") as f:
                f.write(b"mockaudio")

            with patch("shutil.which", return_value="/usr/bin/pw-play"), patch("subprocess.Popen") as mock_popen:
                assert adapter.play_pronunciation("你好") is True
                mock_popen.assert_called_once()

