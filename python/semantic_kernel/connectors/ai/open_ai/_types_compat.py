# Copyright (c) Microsoft. All rights reserved.

"""Compatibility helpers for OpenAI client private type exports.

Some OpenAI SDK 2.x releases expose ``omit`` while others only expose
``NOT_GIVEN``. Semantic Kernel uses this sentinel for optional file/mask
parameters, so we normalize both variants here.
"""

from openai._types import FileTypes

try:
    from openai._types import Omit, omit
except ImportError:  # pragma: no cover - exercised via compatibility unit test
    from openai._types import NOT_GIVEN, NotGiven

    Omit = NotGiven
    omit = NOT_GIVEN

__all__ = ["FileTypes", "Omit", "omit"]
