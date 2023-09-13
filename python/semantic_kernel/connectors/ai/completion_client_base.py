# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from logging import Logger
from typing import Optional

from pydantic import Field

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.utils.null_logger import NullLogger


class CompletionClientBase(SKBaseModel, ABC):
    prompt_tokens: Optional[int] = Field(default=0, init=False)
    completion_tokens: Optional[int] = Field(default=0, init=False)
    total_tokens: Optional[int] = Field(default=0, init=False)
    log: Logger = Field(default_factory=NullLogger)

    def capture_usage_details(
        self, prompt_tokens: int = 0, completion_tokens: int = 0, total_tokens: int = 0
    ) -> None:
        """
        Adds tokens to the total number of tokens used.

        Arguments:
            prompt_tokens {int} -- The number of tokens used for the prompts.
            completion_tokens {int} -- The number of tokens used for the completions.
            total_tokens {int} -- The total number of tokens used.
        """
        self.log.info(
            f"{self.__class__.__name__} service used {total_tokens} tokens for this request"
        )
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += total_tokens
