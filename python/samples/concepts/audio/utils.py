# Copyright (c) Microsoft. All rights reserved.

import logging

import sounddevice as sd

logger = logging.getLogger(__name__)


def check_audio_devices():
    logger.debug(sd.query_devices())
