# Copyright (c) Microsoft. All rights reserved.

import logging

from semantic_kernel.utils.logging import setup_logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
setup_logging()
