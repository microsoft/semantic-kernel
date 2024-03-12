import pytest
import logging

from charset_normalizer.utils import set_logging_handler
from charset_normalizer.api import from_bytes, explain_handler
from charset_normalizer.constant import TRACE


class TestLogBehaviorClass:
    def setup(self):
        self.logger = logging.getLogger("charset_normalizer")
        self.logger.handlers.clear()
        self.logger.addHandler(logging.NullHandler())
        self.logger.level = logging.WARNING

    def test_explain_true_behavior(self, caplog):
        test_sequence = b'This is a test sequence of bytes that should be sufficient'
        from_bytes(test_sequence, steps=1, chunk_size=50, explain=True)
        assert explain_handler not in self.logger.handlers
        for record in caplog.records:
            assert record.levelname in ["Level 5", "DEBUG"]

    def test_explain_false_handler_set_behavior(self, caplog):
        test_sequence = b'This is a test sequence of bytes that should be sufficient'
        set_logging_handler(level=TRACE, format_string="%(message)s")
        from_bytes(test_sequence, steps=1, chunk_size=50, explain=False)
        assert any(isinstance(hdl, logging.StreamHandler) for hdl in self.logger.handlers)
        for record in caplog.records:
            assert record.levelname in ["Level 5", "DEBUG"]
        assert "Encoding detection: ascii is most likely the one." in caplog.text

    def test_set_stream_handler(self, caplog):
        set_logging_handler(
            "charset_normalizer", level=logging.DEBUG
        )
        self.logger.debug("log content should log with default format")
        for record in caplog.records:
            assert record.levelname in ["Level 5", "DEBUG"]
        assert "log content should log with default format" in caplog.text

    def test_set_stream_handler_format(self, caplog):
        set_logging_handler(
            "charset_normalizer", format_string="%(message)s"
        )
        self.logger.info("log content should only be this message")
        assert caplog.record_tuples == [
            (
                "charset_normalizer",
                logging.INFO,
                "log content should only be this message",
            )
        ]
