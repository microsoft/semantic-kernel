# Copyright (c) Microsoft. All rights reserved.

import logging


def setup_logging():
    """Setup a detailed logging format."""
    logging.basicConfig(
        format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
