# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from logging import Logger
from typing import Optional

from pydantic import constr, validator

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.utils.null_logger import NullLogger


class AIServiceClientBase(SKBaseModel, ABC):
    model_id: constr(strip_whitespace=True, min_length=1)
    log: Optional[Logger]

    @validator("log", pre=True)
    def validate_log(cls, v):
        return v or NullLogger()
