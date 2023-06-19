from logging import Logger
from typing import List

from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.guidance_block import GuidanceBlock
from semantic_kernel.template_engine.blocks.symbols import Symbols
from semantic_kernel.template_engine.code_tokenizer import CodeTokenizer
from semantic_kernel.utils.null_logger import NullLogger


class GuidanceCodeTokener(CodeTokenizer):
    def __init__(
        self,
        log: Logger = NullLogger(),
    ):
        super().__init__(log)

    def tokenize(self, text: str) -> List[Block]:
        blocks = []
        if self._is_guidance_block(text):
            blocks.append(GuidanceBlock(text, self.log))
            return blocks
        return super().tokenize(text)

    def _is_guidance_block(self, text: str) -> bool:
        start_with_symbols = text.startswith(
            (
                Symbols.GUIDANCE_BLOCK_PREFIX_GEN,
                Symbols.GUIDANCE_BLOCK_PREFIX_SELECT,
                Symbols.GUIDANCE_BLOCK_HB_START,
                Symbols.GUIDANCE_BLOCK_HB_END,
                Symbols.GUIDANCE_BLOCK_HB_VAR,
                Symbols.GUIDANCE_BLOCK_HB_TILD,
            )
        )
        if start_with_symbols:
            return True

        return text in (
            Symbols.GUIDANCE_BLOCK_OR_KW,
            Symbols.GUIDANCE_BLOCK_AND_KW,
        )
