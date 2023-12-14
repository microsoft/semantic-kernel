# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, List, Optional

from pydantic import PrivateAttr

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.code_block import CodeBlock
from semantic_kernel.template_engine.blocks.symbols import Symbols
from semantic_kernel.template_engine.blocks.text_block import TextBlock
from semantic_kernel.template_engine.code_tokenizer import CodeTokenizer

logger: logging.Logger = logging.getLogger(__name__)


# BNF parsed by TemplateTokenizer:
# [template]       ::= "" | [block] | [block] [template]
# [block]          ::= [sk-block] | [text-block]
# [sk-block]       ::= "{{" [variable] "}}"
#                      | "{{" [value] "}}"
#                      | "{{" [function-call] "}}"
# [text-block]     ::= [any-char] | [any-char] [text-block]
# [any-char]       ::= any char
class TemplateTokenizer(SKBaseModel):
    _code_tokenizer: CodeTokenizer = PrivateAttr()

    def __init__(self, log: Optional[Any] = None):
        super().__init__()
        if log:
            logger.warning(
                "The `log` parameter is deprecated. Please use the `logging` module instead."
            )
        self._code_tokenizer = CodeTokenizer()

    def tokenize(self, text: str) -> List[Block]:
        # An empty block consists of 4 chars: "{{}}"
        EMPTY_CODE_BLOCK_LENGTH = 4
        # A block shorter than 5 chars is either empty or
        # invalid, e.g. "{{ }}" and "{{$}}"
        MIN_CODE_BLOCK_LENGTH = EMPTY_CODE_BLOCK_LENGTH + 1

        text = text or ""

        # Render None/empty to ""
        if not text or text == "":
            return [TextBlock.from_text("")]

        # If the template is "empty" return it as a text block
        if len(text) < MIN_CODE_BLOCK_LENGTH:
            return [TextBlock.from_text(text)]

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

            # When "{{" is found outside a value
            # Note: "{{ {{x}}" => ["{{ ", "{{x}}"]
            if (
                not inside_text_value
                and current_char == Symbols.BLOCK_STARTER
                and next_char == Symbols.BLOCK_STARTER
            ):
                # A block starts at the first "{"
                block_start_pos = current_char_pos
                block_start_found = True

            # After having found "{{"
            if block_start_found:
                # While inside a text value, when the end quote is found
                if inside_text_value:
                    if current_char == Symbols.ESCAPE_CHAR and self._can_be_escaped(
                        next_char
                    ):
                        skip_next_char = True
                        continue

                    if current_char == text_value_delimiter:
                        inside_text_value = False
                else:
                    # A value starts here
                    if current_char in (Symbols.DBL_QUOTE, Symbols.SGL_QUOTE):
                        inside_text_value = True
                        text_value_delimiter = current_char
                    # If the block ends here
                    elif (
                        current_char == Symbols.BLOCK_ENDER
                        and next_char == Symbols.BLOCK_ENDER
                    ):
                        # If there is plain text between the current
                        # var/val/code block and the previous one,
                        # add it as a text block
                        if block_start_pos > end_of_last_block:
                            blocks.append(
                                TextBlock.from_text(
                                    text,
                                    end_of_last_block,
                                    block_start_pos,
                                )
                            )

                        # Extract raw block
                        content_with_delimiters = text[
                            block_start_pos : cursor + 1
                        ]  # noqa: E203
                        # Remove "{{" and "}}" delimiters and trim whitespace
                        content_without_delimiters = content_with_delimiters[
                            2:-2
                        ].strip()

                        if len(content_without_delimiters) == 0:
                            # If what is left is empty, consider the raw block
                            # a TextBlock
                            blocks.append(TextBlock.from_text(content_with_delimiters))
                        else:
                            code_blocks = self._code_tokenizer.tokenize(
                                content_without_delimiters
                            )

                            first_block_type = code_blocks[0].type

                            if first_block_type == BlockTypes.VARIABLE:
                                if len(code_blocks) > 1:
                                    raise ValueError(
                                        "Invalid token detected after the "
                                        f"variable: {content_without_delimiters}"
                                    )

                                blocks.append(code_blocks[0])
                            elif first_block_type == BlockTypes.VALUE:
                                if len(code_blocks) > 1:
                                    raise ValueError(
                                        "Invalid token detected after the "
                                        "value: {content_without_delimiters}"
                                    )

                                blocks.append(code_blocks[0])
                            elif first_block_type == BlockTypes.FUNCTION_ID:
                                if len(code_blocks) > 2:
                                    raise ValueError(
                                        "Functions support only one "
                                        f"parameter: {content_without_delimiters}"
                                    )

                                blocks.append(
                                    CodeBlock(
                                        content_without_delimiters,
                                        code_blocks,
                                    )
                                )
                            else:
                                raise ValueError(
                                    "Code tokenizer returned an incorrect "
                                    f"first token type {first_block_type}"
                                )

                        end_of_last_block = cursor + 1
                        block_start_found = False

        # If there is something left after the last block, capture it as a TextBlock
        if end_of_last_block < len(text):
            blocks.append(TextBlock.from_text(text, end_of_last_block, len(text)))

        return blocks

    def _can_be_escaped(self, c: str) -> bool:
        return c in (
            Symbols.DBL_QUOTE,
            Symbols.SGL_QUOTE,
            Symbols.ESCAPE_CHAR,
        )
