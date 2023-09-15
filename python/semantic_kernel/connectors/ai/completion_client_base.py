# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from logging import Logger

from pydantic import Field

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.utils.null_logger import NullLogger


class CompletionClientBase(SKBaseModel, ABC):
    log: Logger = Field(default_factory=NullLogger)
