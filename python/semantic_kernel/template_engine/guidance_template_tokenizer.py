from logging import Logger
from typing import List
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.guidance_block import GuidanceBlock

from semantic_kernel.template_engine.blocks.symbols import Symbols
from semantic_kernel.template_engine.guidance_code_tokenizer import GuidanceCodeTokener
from semantic_kernel.template_engine.template_tokenizer import TemplateTokenizer
from semantic_kernel.utils.null_logger import NullLogger


class GuidanceTemplateTokenizer(TemplateTokenizer):
    def __init__(self, log: Logger = NullLogger()):
        super().__init__(log)
        self.code_tokenizer = GuidanceCodeTokener(log)
