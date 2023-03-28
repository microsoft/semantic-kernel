# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List

from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.code_block import CodeBlock
from semantic_kernel.template_engine.blocks.symbols import Symbols
from semantic_kernel.template_engine.blocks.text_block import TextBlock
from semantic_kernel.template_engine.code_tokenizer import CodeTokenizer
from semantic_kernel.utils.null_logger import NullLogger


class TemplateTokenizer:
    def __init__(self, log: Logger = None):
        self.log = log or NullLogger()
        self.code_tokenizer = CodeTokenizer(self.log)

    def tokenize(self, text: str) -> List[Block]:
        EMPTY_CODE_BLOCK_LENGTH = 4
        MIN_CODE_BLOCK_LENGTH = EMPTY_CODE_BLOCK_LENGTH + 1

        text = text or ""

        if not text:
            return [TextBlock("", log=self.log)]

        if len(text) < MIN_CODE_BLOCK_LENGTH:
            return [TextBlock(text, log=self.log)]

        blocks = []
        end_of_last_block = 0
        block_start_pos = 0
        block_start_found = False
        inside_text_value = False
        text_value_delimiter = None
        skip_next_char = False
        next_char = text[0]

        for next_char_cursor in range(1, len(text)):
            current_char_pos = next_char_cursor - 1
            cursor = next_char_cursor
            current_char = next_char
            next_char = text[next_char_cursor]

            if skip_next_char:
                skip_next_char = False
                continue

            if (
                not inside_text_value
                and current_char == Symbols.BLOCK_STARTER
                and next_char == Symbols.BLOCK_STARTER
            ):
                block_start_pos = current_char_pos
                block_start_found = True

            if block_start_found:
                if inside_text_value:
                    if current_char == Symbols.ESCAPE_CHAR and self._can_be_escaped(
                        next_char
                    ):
                        skip_next_char = True
                        continue

                    if current_char == text_value_delimiter:
                        inside_text_value = False
                else:
                    if current_char in (Symbols.DBL_QUOTE, Symbols.SGL_QUOTE):
                        inside_text_value = True
                        text_value_delimiter = current_char
                    elif (
                        current_char == Symbols.BLOCK_ENDER
                        and next_char == Symbols.BLOCK_ENDER
                    ):
                        if block_start_pos > end_of_last_block:
                            blocks.append(
                                TextBlock(
                                    text,
                                    end_of_last_block,
                                    block_start_pos,
                                    log=self.log,
                                )
                            )

                        content_with_delimiters = text[block_start_pos : cursor + 1]
                        content_without_delimiters = content_with_delimiters[
                            2:-2
                        ].strip()

                        if not content_without_delimiters:
                            blocks.append(
                                TextBlock(content_with_delimiters, log=self.log)
                            )
                        else:
                            code_blocks = self.code_tokenizer.tokenize(
                                content_without_delimiters
                            )

                            first_block_type = code_blocks[0].type

                            if first_block_type == BlockTypes.VARIABLE:
                                if len(code_blocks) > 1:
                                    raise ValueError(
                                        f"Invalid token detected after the variable: {content_without_delimiters}"
                                    )

                                blocks.append(code_blocks[0])
                            elif first_block_type == BlockTypes.VALUE:
                                if len(code_blocks) > 1:
                                    raise ValueError(
                                        f"Invalid token detected after the value: {content_without_delimiters}"
                                    )

                                blocks.append(code_blocks[0])
                            elif first_block_type == BlockTypes.FUNCTION_ID:
                                if len(code_blocks) > 2:
                                    raise ValueError(
                                        f"Functions support only one parameter: {content_without_delimiters}"
                                    )

                                blocks.append(
                                    CodeBlock(
                                        content_without_delimiters,
                                        code_blocks,
                                        self.log,
                                    )
                                )
                            else:
                                raise ValueError(
                                    f"Code tokenizer returned an incorrect first token type {first_block_type}"
                                )

                        end_of_last_block = cursor + 1
                        block_start_found = False

        if end_of_last_block < len(text):
            blocks.append(TextBlock(text, end_of_last_block, len(text), log=self.log))

        return blocks

    def _is_quote(self, c: str) -> bool:
        return c in (Symbols.DBL_QUOTE, Symbols.SGL_QUOTE)

    def _can_be_escaped(self, c: str) -> bool:
        return c in (
            Symbols.DBL_QUOTE,
            Symbols.SGL_QUOTE,
            Symbols.ESCAPE_CHAR,
        )
