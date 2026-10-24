import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_DEFAULT_LOG_FILE = "moon_shang.log"


def setup_logger(
    name: str = "moon_shang",
    log_file: str = _DEFAULT_LOG_FILE,
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 3,
) -> logging.Logger:
    """Configura y retorna un logger estructurado con salida a consola y archivo rotativo."""
    logger = logging.getLogger(name)

    env_level = os.getenv("LOG_LEVEL", "").upper()
    if env_level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        level = getattr(logging, env_level)

    logger.setLevel(level)

    # Evitar duplicar handlers si ya está configurado
    if logger.handlers:
        return logger

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # 1. Handler para consola estándar
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # 2. Handler rotativo a fichero
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    except OSError as e:
        logger.warning("No se pudo inicializar el fichero de log rotativo (%s): %s", log_file, e)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """Obtiene un logger hijo asociado a un módulo específico."""
    root = logging.getLogger("moon_shang")
    if not root.handlers:
        setup_logger()
    return logging.getLogger(f"moon_shang.{module_name}")
