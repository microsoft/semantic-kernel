# Copyright (c) Microsoft. All rights reserved.

import logging
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

from semantic_kernel.exceptions import (
    BlockSyntaxError,
    CodeBlockTokenError,
    TemplateSyntaxError,
)
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from semantic_kernel.template_engine.blocks.block import Block
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
from typing import List

>>>>>>> ms/small_fixes
<<<<<<< head
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
from typing import List

>>>>>>> ms/small_fixes
>>>>>>> Stashed changes
>>>>>>> origin/main
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_errors import (
    CodeBlockSyntaxError,
    CodeBlockTokenError,
    FunctionIdBlockSyntaxError,
    TemplateSyntaxError,
    ValBlockSyntaxError,
    VarBlockSyntaxError,
)
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
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
class TemplateTokenizer:
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    """Tokenize the template text into blocks."""

    @staticmethod
    def tokenize(text: str) -> list[Block]:
        """Tokenize the template text into blocks."""
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
    @staticmethod
    def tokenize(text: str) -> List[Block]:
>>>>>>> ms/small_fixes
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< main
=======
=======
    @staticmethod
    def tokenize(text: str) -> List[Block]:
>>>>>>> ms/small_fixes
>>>>>>> Stashed changes
>>>>>>> origin/main
        code_tokenizer = CodeTokenizer()
        # An empty block consists of 4 chars: "{{}}"
        EMPTY_CODE_BLOCK_LENGTH = 4
        # A block shorter than 5 chars is either empty or
        # invalid, e.g. "{{ }}" and "{{$}}"
        MIN_CODE_BLOCK_LENGTH = EMPTY_CODE_BLOCK_LENGTH + 1

        text = text or ""

        # Render None/empty to ""
        if not text:
            return [TextBlock.from_text("")]

        # If the template is "empty" return it as a text block
        if len(text) < MIN_CODE_BLOCK_LENGTH:
            return [TextBlock.from_text(text)]

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        blocks: list[Block] = []
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        blocks: list[Block] = []
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
        blocks: list[Block] = []
=======
>>>>>>> Stashed changes
<<<<<<< main
        blocks: list[Block] = []
=======
        blocks: List[Block] = []
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
        end_of_last_block = 0
        block_start_pos = 0
        block_start_found = False
        inside_text_value = False
        text_value_delimiter = None
        skip_next_char = False

        for current_char_pos, current_char in enumerate(text[:-1]):
            next_char_pos = current_char_pos + 1
            next_char = text[next_char_pos]

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

            if not block_start_found:
                continue
            # After having found "{{"
            if inside_text_value:
                # While inside a text value, when the end quote is found
                # If the current char is escaping the next special char we skip
                if current_char == Symbols.ESCAPE_CHAR and next_char in (
                    Symbols.DBL_QUOTE,
                    Symbols.SGL_QUOTE,
                    Symbols.ESCAPE_CHAR,
                ):
                    skip_next_char = True
                    continue

                if current_char == text_value_delimiter:
                    inside_text_value = False
                continue

            # A value starts here
            if current_char in (Symbols.DBL_QUOTE, Symbols.SGL_QUOTE):
                inside_text_value = True
                text_value_delimiter = current_char
                continue
            # If the block ends here
            if current_char == Symbols.BLOCK_ENDER and next_char == Symbols.BLOCK_ENDER:
                blocks.extend(
                    TemplateTokenizer._extract_blocks(
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
                        text,
                        code_tokenizer,
                        block_start_pos,
                        end_of_last_block,
                        next_char_pos,
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
                        text, code_tokenizer, block_start_pos, end_of_last_block, next_char_pos
>>>>>>> ms/small_fixes
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
                        text, code_tokenizer, block_start_pos, end_of_last_block, next_char_pos
>>>>>>> ms/small_fixes
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
                    )
                )
                end_of_last_block = next_char_pos + 1
                block_start_found = False

        # If there is something left after the last block, capture it as a TextBlock
        if end_of_last_block < len(text):
            blocks.append(TextBlock.from_text(text, end_of_last_block, len(text)))

        return blocks

    @staticmethod
    def _extract_blocks(
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
        text: str,
        code_tokenizer: CodeTokenizer,
        block_start_pos: int,
        end_of_last_block: int,
        next_char_pos: int,
    ) -> list[Block]:
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
        text: str, code_tokenizer: CodeTokenizer, block_start_pos: int, end_of_last_block: int, next_char_pos: int
    ) -> List[Block]:
>>>>>>> ms/small_fixes
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< main
=======
=======
        text: str, code_tokenizer: CodeTokenizer, block_start_pos: int, end_of_last_block: int, next_char_pos: int
    ) -> List[Block]:
>>>>>>> ms/small_fixes
>>>>>>> Stashed changes
>>>>>>> origin/main
        """Extract the blocks from the found code.

        If there is text before the current block, create a TextBlock from that.

        If the block is empty, return a TextBlock with the delimiters.

        If the block is not empty, tokenize it and return the result.
        If there is only a variable or value in the code block,
        return just that, instead of the CodeBlock.
        """
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        new_blocks: list[Block] = []
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        new_blocks: list[Block] = []
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
        new_blocks: list[Block] = []
=======
>>>>>>> Stashed changes
<<<<<<< main
        new_blocks: list[Block] = []
=======
        new_blocks: List[Block] = []
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
        if block_start_pos > end_of_last_block:
            new_blocks.append(
                TextBlock.from_text(
                    text,
                    end_of_last_block,
                    block_start_pos,
                )
            )

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        content_with_delimiters = text[block_start_pos : next_char_pos + 1]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        content_with_delimiters = text[block_start_pos : next_char_pos + 1]
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
        content_with_delimiters = text[block_start_pos : next_char_pos + 1]
=======
>>>>>>> Stashed changes
<<<<<<< main
        content_with_delimiters = text[block_start_pos : next_char_pos + 1]
=======
        content_with_delimiters = text[block_start_pos : next_char_pos + 1]  # noqa: E203
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
        content_without_delimiters = content_with_delimiters[2:-2].strip()

        if len(content_without_delimiters) == 0:
            # If what is left is empty (only {{}}), consider the raw block
            # a TextBlock
            new_blocks.append(TextBlock.from_text(content_with_delimiters))
            return new_blocks

        try:
            code_blocks = code_tokenizer.tokenize(content_without_delimiters)
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        except BlockSyntaxError as e:
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        except BlockSyntaxError as e:
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
        except BlockSyntaxError as e:
=======
>>>>>>> Stashed changes
<<<<<<< main
        except BlockSyntaxError as e:
=======
        except (
            CodeBlockTokenError,
            CodeBlockSyntaxError,
            VarBlockSyntaxError,
            ValBlockSyntaxError,
            FunctionIdBlockSyntaxError,
        ) as e:
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
            msg = f"Failed to tokenize code block: {content_without_delimiters}. {e}"
            logger.warning(msg)
            raise TemplateSyntaxError(msg) from e

        if code_blocks[0].type in (
            BlockTypes.VALUE,
            BlockTypes.VARIABLE,
        ):
            new_blocks.append(code_blocks[0])
            return new_blocks
        try:
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            new_blocks.append(
                CodeBlock(content=content_without_delimiters, tokens=code_blocks)
            )
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            new_blocks.append(
                CodeBlock(content=content_without_delimiters, tokens=code_blocks)
            )
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< main
            new_blocks.append(
                CodeBlock(content=content_without_delimiters, tokens=code_blocks)
            )
=======
            new_blocks.append(CodeBlock(content=content_without_delimiters, tokens=code_blocks))
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
            return new_blocks
        except CodeBlockTokenError as e:
            msg = f"Failed to tokenize code block: {content_without_delimiters}. {e}"
            logger.warning(msg)
            raise TemplateSyntaxError(msg) from e
