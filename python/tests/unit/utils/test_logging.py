# Copyright (c) Microsoft. All rights reserved.

import logging

from semantic_kernel.utils.logging import setup_logging


def test_setup_logging():
    """Test that the logging is setup correctly."""
    setup_logging()

    root_logger = logging.getLogger()
    assert root_logger.handlers
    assert any(
        isinstance(handler, logging.StreamHandler) for handler in root_logger.handlers
    )
