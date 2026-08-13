import logging
import os
import tempfile
from unittest.mock import patch

from engine.logger import _reset_setup, get_logger, setup_logging


class TestLogger:
    def setup_method(self):
        _reset_setup()

    def teardown_method(self):
        _reset_setup()

    def test_setup_logging_creates_log_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = os.path.join(tmpdir, "logs")
            with patch("engine.logger.LOGS_DIR", logs_dir):
                setup_logging()
                files = os.listdir(logs_dir)
                _reset_setup()
            assert len(files) == 1
            assert files[0] == "autokeymouse.log"

    def test_get_logger_returns_logger_with_correct_name(self):
        logger = get_logger("engine.recorder")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "autokeymouse.engine.recorder"

    def test_get_logger_returns_same_instance(self):
        a = get_logger("engine.recorder")
        b = get_logger("engine.recorder")
        assert a is b

    def test_logger_writes_to_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = os.path.join(tmpdir, "logs")
            with patch("engine.logger.LOGS_DIR", logs_dir):
                setup_logging()
                logger = get_logger("test")
                logger.info("hello world")
                log_file = os.path.join(logs_dir, os.listdir(logs_dir)[0])
                _reset_setup()
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
            assert "hello world" in content
            assert "[INFO]" in content
            assert "test:" in content

    def test_setup_logging_respects_level(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = os.path.join(tmpdir, "logs")
            with patch("engine.logger.LOGS_DIR", logs_dir):
                setup_logging(level=logging.WARNING)
                logger = get_logger("test")
                logger.debug("should not appear")
                logger.warning("should appear")
                log_file = os.path.join(logs_dir, os.listdir(logs_dir)[0])
                _reset_setup()
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
            assert "should not appear" not in content
            assert "should appear" in content

    def test_setup_logging_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = os.path.join(tmpdir, "logs")
            with patch("engine.logger.LOGS_DIR", logs_dir):
                setup_logging()
                files_before = os.listdir(logs_dir)
                setup_logging()
                files_after = os.listdir(logs_dir)
                _reset_setup()
            assert len(files_before) == len(files_after)