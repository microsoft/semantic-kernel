# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from re import match as regex_match
from typing import Optional, Tuple

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.var_block import VarBlock
from semantic_kernel.template_engine.template_exception import TemplateException


class CodeBlock(Block):
    _validated: bool = False

    def __init__(self, content: str, log: Logger) -> None:
        super().__init__(BlockTypes.Code, content, log)

    def _is_valid_function_name(self, name: str) -> bool:
        return regex_match(r"^[a-zA-Z_][a-zA-Z0-9_.]*$", name) is not None

    def is_valid(self) -> Tuple[bool, str]:
        error = ""

        if self._content is None:
            error = "This code block's content is None"
        elif self._content.strip() == "":
            error = "This code block's content is empty"

        if error != "":
            self._log.error(error)
            return False, error

        # split content on ' ', '\t', '\r', and '\n' and
        # remove any empty parts
        parts = [part for part in self._content.split() if part != ""]

        for index, part in enumerate(parts):
            if index == 0:  # there is only a function name
                if VarBlock.has_var_prefix(part):
                    error = f"Variables cannot be used as function names [`{part}`]"
                    break

                if not self._is_valid_function_name(part):
                    error = f"Invalid function name [`{part}`]"
                    break
            else:  # the function has parameters
                if not VarBlock.has_var_prefix(part):
                    error = (
                        f"[`{part}`] is not a valid function parameter: "
                        "parameters must be valid variables (invalid prefix)."
                    )
                    break
                if len(part) < 2:
                    error = (
                        f"[`{part}`] is not a valid function parameter: "
                        "parameters must be valid variables (too short)."
                    )
                if not VarBlock.is_valid_var_name(part[1:]):
                    error = (
                        f"[`{part}`] is not a valid function parameter: "
                        "parameters must be valid variables (invalid characters)."
                    )
                    break

        if error != "":
            self._log.error(error)
            return False, error

        self._validated = True
        return True, ""

    def render(self, variable: Optional[ContextVariables]) -> str:
        raise NotImplementedError(
            "Code block rendering requires using the render_code_async method call."
        )

    async def render_code_async(self, context: SKContext) -> str:
        if not self._validated:
            valid, error = self.is_valid()
            if not valid:
                raise TemplateException(TemplateException.ErrorCodes.SyntaxError, error)

        self._log.debug(f"Rendering code block: `{self._content}`")

        parts = [part for part in self._content.split() if part != ""]
        function_name = parts[0]

        context.throw_if_skill_collection_not_set()
        # hack to get types to check, should never fail
        assert context.skills is not None
        found, function = self._get_function_from_skill_collection(
            context.skills, function_name
        )

        if not found:
            self._log.warning(f"Function not found: `{function_name}`")
            return ""
        assert function is not None  # for type checker

        if context.variables is None:
            self._log.error("Context variables are not set")
            return ""

        variables_clone = context.variables.clone()
        if len(parts) > 1:
            self._log.debug(f"Passing required parameter: `{parts[1]}`")
            value = VarBlock(parts[1], self._log).render(variables_clone)
            variables_clone.update(value)

        result = await function.invoke_with_custom_input_async(
            variables_clone, context.memory, context.skills, self._log
        )

        if result.error_occurred:
            self._log.error(
                "Semantic function references a function `{function_name}` "
                f"of incompatible type `{function.__class__.__name__}`"
            )
            return ""

        return result.result

    def _get_function_from_skill_collection(
        self, skills: ReadOnlySkillCollectionBase, function_name: str
    ) -> Tuple[bool, Optional[SKFunctionBase]]:
        if skills.has_native_function(None, function_name):
            return True, skills.get_native_function(None, function_name)

        if "." in function_name:
            parts = function_name.split(".")
            if len(parts) > 2:
                self._log.error(f"Invalid function name: `{function_name}`")
                raise TemplateException(
                    TemplateException.ErrorCodes.SyntaxError,
                    f"Invalid function name: `{function_name}`"
                    "A function name can only contain one `.` to "
                    "delineate the skill name from the function name.",
                )

            skill_name, function_name = parts
            if skills.has_native_function(skill_name, function_name):
                return True, skills.get_native_function(skill_name, function_name)

            if skills.has_semantic_function(skill_name, function_name):
                return True, skills.get_semantic_function(skill_name, function_name)

        return False, None
