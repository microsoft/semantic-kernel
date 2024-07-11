# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional, Tuple

import pydantic as pdt

from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine.code_tokenizer import CodeTokenizer


class CodeBlock(Block):
    _tokens: List[Block] = pdt.PrivateAttr()
    _validated: bool = pdt.PrivateAttr(default=False)

    def __init__(
        self,
        content: str,
        tokens: Optional[List[Block]] = None,
        log: Optional[Logger] = None,
    ):
        super().__init__(content=content and content.strip(), log=log)

        self._tokens = tokens or CodeTokenizer(log).tokenize(content)
        self._validated = False

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.CODE

    def is_valid(self) -> Tuple[bool, str]:
        error_msg = ""

        for token in self._tokens:
            is_valid, error_msg = token.is_valid()
            if not is_valid:
                self.log.error(error_msg)
                return False, error_msg

        if len(self._tokens) > 1:
            if self._tokens[0].type != BlockTypes.FUNCTION_ID:
                error_msg = f"Unexpected second token found: {self._tokens[1].content}"
                self.log.error(error_msg)
                return False, error_msg

            if (
                self._tokens[1].type != BlockTypes.VALUE
                and self._tokens[1].type != BlockTypes.VARIABLE
            ):
                error_msg = "Functions support only one parameter"
                self.log.error(error_msg)
                return False, error_msg

        if len(self._tokens) > 2:
            error_msg = f"Unexpected second token found: {self._tokens[1].content}"
            self.log.error(error_msg)
            return False, error_msg

        self._validated = True

        return True, ""

    async def render_code_async(self, context):
        if not self._validated:
            is_valid, error = self.is_valid()
            if not is_valid:
                raise ValueError(error)

        self.log.debug(f"Rendering code: `{self.content}`")

        if self._tokens[0].type in (BlockTypes.VALUE, BlockTypes.VARIABLE):
            return self._tokens[0].render(context.variables)

        if self._tokens[0].type == BlockTypes.FUNCTION_ID:
            return await self._render_function_call_async(self._tokens[0], context)

        raise ValueError(f"Unexpected first token type: {self._tokens[0].type}")

    async def _render_function_call_async(self, f_block: FunctionIdBlock, context):
        if not context.skills:
            raise ValueError("Skill collection not set")

        function = self._get_function_from_skill_collection(context.skills, f_block)

        if not function:
            error_msg = f"Function `{f_block.content}` not found"
            self.log.error(error_msg)
            raise ValueError(error_msg)

        variables_clone = context.variables.clone()

        if len(self._tokens) > 1:
            self.log.debug(f"Passing variable/value: `{self._tokens[1].content}`")
            input_value = self._tokens[1].render(variables_clone)
            variables_clone.update(input_value)

        result = await function.invoke_async(
            variables=variables_clone, memory=context.memory, log=self.log
        )

        if result.error_occurred:
            error_msg = (
                f"Function `{f_block.content}` execution failed. "
                f"{result.last_exception.__class__.__name__}: "
                f"{result.last_error_description}"
            )
            self.log.error(error_msg)
            raise ValueError(error_msg)

        return result.result

    def _get_function_from_skill_collection(
        self, skills: ReadOnlySkillCollectionBase, f_block: FunctionIdBlock
    ) -> Optional[SKFunctionBase]:
        if not f_block.skill_name and skills.has_function(None, f_block.function_name):
            return skills.get_function(None, f_block.function_name)

        if f_block.skill_name and skills.has_function(
            f_block.skill_name, f_block.function_name
        ):
            return skills.get_function(f_block.skill_name, f_block.function_name)

        return None
