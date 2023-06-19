# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional
from semantic_kernel.template_engine.guidance_template_tokenizer import (
    GuidanceTemplateTokenizer,
)

from semantic_kernel.template_engine.template_tokenizer import TemplateTokenizer
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.template_engine.prompt_template_engine import PromptTemplateEngine


class GuidanceTemplateEngine(PromptTemplateEngine):
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self._logger = logger or NullLogger()
        self._tokenizer = GuidanceTemplateTokenizer(self._logger)
