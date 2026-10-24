import hashlib
import os
import shutil
import subprocess
import urllib.parse
import urllib.request

from core.logger import get_logger
from domain.ports import ITextToSpeech

logger = get_logger("tts")


class GoogleTTSAudioAdapter(ITextToSpeech):
    """Adaptador de Text-to-Speech gratuito usando Google TTS y caché local de audio."""

    def __init__(self, cache_dir: str | None = None):
        if cache_dir is None:
            home = os.path.expanduser("~")
            self.cache_dir = os.path.join(home, ".cache", "moon_shang", "audio")
        else:
            self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self._qt_player = None
        self._qt_output = None

    def _get_cache_path(self, text_zh: str) -> str:
        h = hashlib.sha256(text_zh.encode("utf-8")).hexdigest()[:16]
        return os.path.join(self.cache_dir, f"{h}.mp3")

    def download_audio(self, text_zh: str) -> str | None:
        """Descarga el archivo de audio MP3 si no está en caché y retorna su ruta."""
        path = self._get_cache_path(text_zh)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            logger.debug("Audio en caché encontrado para '%s': %s", text_zh, path)
            return path

        encoded = urllib.parse.quote(text_zh)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded}&tl=zh-CN&client=tw-ob"
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "translate.google.com":
            logger.error("Intento de petición a esquema o dominio no permitido: %s", url)
            return None

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:  # nosec B310
                data = resp.read()
                if not data:
                    logger.warning("Respuesta vacía al descargar TTS para '%s'", text_zh)
                    return None

            temp_path = f"{path}.tmp"
            with open(temp_path, "wb") as f:
                f.write(data)
            os.replace(temp_path, path)
            logger.info("Audio TTS descargado y guardado en caché: %s (%d bytes)", path, len(data))
            return path
        except Exception:
            logger.exception("Fallo al descargar audio de pronunciación para '%s'", text_zh)
            return None

    def play_pronunciation(self, text_zh: str) -> bool:
        """Reproduce la pronunciación localmente usando un reproductor nativo."""
        if not text_zh or not isinstance(text_zh, str) or not text_zh.strip():
            logger.warning("Texto vacío proporcionado para reproducción de pronunciación.")
            return False

        cleaned = text_zh.strip()
        path = self.download_audio(cleaned)
        if not path or not os.path.exists(path):
            logger.warning("No se pudo obtener el archivo de audio para '%s'", cleaned)
            return False

        # 1. Probar reproductores CLI nativos del sistema en orden de preferencia
        players = ["pw-play", "paplay", "aplay", "mpv", "ffplay"]
        for p in players:
            player_bin = shutil.which(p)
            if player_bin:
                try:
                    cmd = [player_bin]
                    if p == "mpv":
                        cmd.extend(["--no-video", "--really-quiet"])
                    elif p == "ffplay":
                        cmd.extend(["-nodisp", "-autoexit", "-loglevel", "quiet"])
                    cmd.append(path)

                    subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                    logger.info("Audio reproducido mediante %s para '%s'", p, cleaned)
                    return True
                except Exception:
                    logger.exception("Error al intentar reproducir con %s", p)
                    continue

        # 2. Respaldo: intentar con PyQt6.QtMultimedia si está en entorno GUI
        try:
            from PyQt6.QtCore import QUrl
            from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
            from PyQt6.QtWidgets import QApplication

            if QApplication.instance():
                self._qt_player = QMediaPlayer()
                self._qt_output = QAudioOutput()
                self._qt_player.setAudioOutput(self._qt_output)
                self._qt_player.setSource(QUrl.fromLocalFile(path))
                self._qt_player.play()
                logger.info("Audio reproducido mediante PyQt6.QtMultimedia para '%s'", cleaned)
                return True
        except Exception:
            logger.exception("Error en fallback de PyQt6.QtMultimedia")

        logger.warning("No se encontró ningún reproductor de audio compatible en el sistema.")
        return False
