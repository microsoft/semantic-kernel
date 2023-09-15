# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from logging import Logger
from typing import Optional

from pydantic import validator

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.utils.null_logger import NullLogger


class CompletionClientBase(SKBaseModel, ABC):
    log: Optional[Logger]

    @validator("log", pre=True)
    def validate_log(cls, v):
        return v or NullLogger()
