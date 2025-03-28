# Copyright (c) Microsoft. All rights reserved.
from enum import Enum


class Status(str, Enum):
    """Status enum."""

    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    INCOMPLETE = "incomplete"
