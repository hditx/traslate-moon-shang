import logging
import os
import tempfile

from core.logger import get_logger, setup_logger


def test_setup_logger_creates_file_and_logs():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test_app.log")
        logger = setup_logger(name="test_logger", log_file=log_file, level=logging.DEBUG)

        logger.info("Mensaje informativo de prueba")
        logger.debug("Mensaje de depuración")

        # Forzar flush
        for handler in logger.handlers:
            handler.flush()

        assert os.path.exists(log_file)
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Mensaje informativo de prueba" in content
        assert "Mensaje de depuración" in content
        assert "[INFO]" in content
        assert "[DEBUG]" in content


def test_logger_records_exception_traceback():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test_err.log")
        logger = setup_logger(name="test_err_logger", log_file=log_file, level=logging.ERROR)

        try:
            _ = 1 / 0
        except ZeroDivisionError:
            logger.exception("Ocurrió un error matemático grave")

        for handler in logger.handlers:
            handler.flush()

        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Ocurrió un error matemático grave" in content
        assert "ZeroDivisionError: division by zero" in content


def test_get_logger_inherits_and_prefixes():
    child_logger = get_logger("submodule")
    assert child_logger.name == "moon_shang.submodule"
