# Copyright (c) Microsoft. All rights reserved.

from typing import List
from logging import Logger

from semantic_kernel.template_engine_v2.blocks.block import Block
from semantic_kernel.template_engine_v2.blocks.symbols import Symbols
from semantic_kernel.template_engine_v2.blocks.val_block import ValBlock
from semantic_kernel.template_engine_v2.blocks.var_block import VarBlock
from semantic_kernel.template_engine_v2.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.utils.null_logger import NullLogger


class CodeTokenizer:
    def __init__(self, log: Logger = None):
        self.log = log or NullLogger()

    def tokenize(self, text: str) -> List[Block]:
        text = text.strip() if text else ""

        if not text:
            return []

        current_token_type = None
        current_token_content = []
        text_value_delimiter = None
        blocks = []
        next_char = text[0]
        space_separator_found = False
        skip_next_char = False

        for next_char_cursor in range(1, len(text)):
            current_char = next_char
            next_char = text[next_char_cursor]

            if skip_next_char:
                skip_next_char = False
                continue

            if next_char_cursor == 1:
                if current_char == Symbols.VAR_PREFIX:
                    current_token_type = "Variable"
                elif current_char in (Symbols.DBL_QUOTE, Symbols.SGL_QUOTE):
                    current_token_type = "Value"
                    text_value_delimiter = current_char
                else:
                    current_token_type = "FunctionId"

                current_token_content.append(current_char)
                continue

            if current_token_type == "Value":
                if current_char == Symbols.ESCAPE_CHAR and self._can_be_escaped(
                    next_char
                ):
                    current_token_content.append(next_char)
                    skip_next_char = True
                    continue

                current_token_content.append(current_char)

                if current_char == text_value_delimiter:
                    blocks.append(ValBlock("".join(current_token_content), self.log))
                    current_token_content.clear()
                    current_token_type = None
                    space_separator_found = False

                continue

            if self._is_blank_space(current_char):
                if current_token_type == "Variable":
                    blocks.append(VarBlock("".join(current_token_content), self.log))
                    current_token_content.clear()
                elif current_token_type == "FunctionId":
                    blocks.append(
                        FunctionIdBlock("".join(current_token_content), self.log)
                    )
                    current_token_content.clear()

                space_separator_found = True
                current_token_type = None

                continue

            current_token_content.append(current_char)

            if current_token_type is None:
                if not space_separator_found:
                    raise ValueError("Tokens must be separated by one space least")

                if current_char in (Symbols.DBL_QUOTE, Symbols.SGL_QUOTE):
                    current_token_type = "Value"
                    text_value_delimiter = current_char
                elif current_char == Symbols.VAR_PREFIX:
                    current_token_type = "Variable"
                else:
                    current_token_type = "FunctionId"

        current_token_content.append(next_char)

        if current_token_type == "Value":
            blocks.append(ValBlock("".join(current_token_content), self.log))
        elif current_token_type == "Variable":
            blocks.append(VarBlock("".join(current_token_content), self.log))
        elif current_token_type == "FunctionId":
            blocks.append(FunctionIdBlock("".join(current_token_content), self.log))
        else:
            raise ValueError("Tokens must be separated by one space least")

        return blocks

    def _is_var_prefix(self, c: str) -> bool:
        return c == Symbols.VAR_PREFIX

    def _is_blank_space(self, c: str) -> bool:
        return c in (
            Symbols.SPACE,
            Symbols.NEW_LINE,
            Symbols.CARRIAGE_RETURN,
            Symbols.TAB,
        )

    def _is_quote(self, c: str) -> bool:
        return c in (Symbols.DBL_QUOTE, Symbols.SGL_QUOTE)

    def _can_be_escaped(self, c: str) -> bool:
        return c in (
            Symbols.DBL_QUOTE,
            Symbols.SGL_QUOTE,
            Symbols.ESCAPE_CHAR,
        )
