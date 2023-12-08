# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import Optional

from pydantic import Field, constr, field_validator

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.utils.null_logger import NullLogger


class AIServiceClientBase(SKBaseModel, ABC):
    """Base class for all AI Services.

    Has a ai_model_id, any other fields have to be defined by the subclasses.

    The ai_model_id can refer to a specific model, like 'gpt-35-turbo' for OpenAI,
    or can just be a string that is used to identify the service.
    """

    ai_model_id: constr(strip_whitespace=True, min_length=1)
