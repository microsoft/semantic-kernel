# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from logging import Logger
from typing import Optional

from pydantic import constr, validator

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.utils.null_logger import NullLogger


class AIServiceClientBase(SKBaseModel, ABC):
    """Base class for all AI Services.

    Has a model_id and a logger, any other fields have to be defined by the subclasses.

    The model_id can refer to a specific model, like 'gpt-35-turbo' for OpenAI,
    or can just be a string that is used to identify the service.
    """

    model_id: constr(strip_whitespace=True, min_length=1)
    log: Optional[Logger] = None

    @validator("log", pre=True)
    def validate_log(cls, v):
        return v or NullLogger()
