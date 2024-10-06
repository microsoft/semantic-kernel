# Copyright (c) Microsoft. All rights reserved.

import logging
from copy import copy
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
>>>>>>> Stashed changes
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import Field, field_validator, model_validator

from semantic_kernel.exceptions import CodeBlockRenderException, CodeBlockTokenError
from semantic_kernel.exceptions.kernel_exceptions import (
    KernelFunctionNotFoundError,
    KernelPluginNotFoundError,
)
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
<<<<<<< Updated upstream
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
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
from typing import TYPE_CHECKING, Any, ClassVar, List, Optional

from pydantic import Field, field_validator, model_validator

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection
>>>>>>> ms/small_fixes
>>>>>>> origin/main
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_errors import CodeBlockRenderError, CodeBlockTokenError
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
>>>>>>> Stashed changes
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine.blocks.named_arg_block import NamedArgBlock
from semantic_kernel.template_engine.code_tokenizer import CodeTokenizer

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

VALID_ARG_TYPES = [BlockTypes.VALUE, BlockTypes.VARIABLE, BlockTypes.NAMED_ARG]


class CodeBlock(Block):
    """Create a code block.

    A code block is a block that usually contains functions to be executed by the kernel.
    It consists of a list of tokens that can be either a function_id, value, a variable or a named argument.

    If the first token is not a function_id but a variable or value, the rest of the tokens will be ignored.
    Only the first argument for the function can be a variable or value, the rest of the tokens have be named arguments.

    Args:
        content: The content of the code block.
        tokens: The list of tokens that compose the code block, if empty, will be created by the CodeTokenizer.

    Raises:
        CodeBlockTokenError: If the content does not contain at least one token.
        CodeBlockTokenError: If the first token is a named argument.
        CodeBlockTokenError: If the second token is not a value or variable.
        CodeBlockTokenError: If a token is not a named argument after the second token.
        CodeBlockRenderError: If the plugin collection is not set in the kernel.
        CodeBlockRenderError: If the function is not found in the plugin collection.
        CodeBlockRenderError: If the function does not take any arguments, but it is being
            called in the template with arguments.
    """

    type: ClassVar[BlockTypes] = BlockTypes.CODE
    tokens: list[Block] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Any) -> Any:
        """Parse the content of the code block and tokenize it.

        If tokens are already present, skip the tokenizing.
        """
        if isinstance(fields, Block) or "tokens" in fields:
            return fields
        content = fields.get("content", "").strip()
        fields["tokens"] = CodeTokenizer.tokenize(content)
        return fields

    @field_validator("tokens", mode="after")
    def check_tokens(cls, tokens: list[Block]) -> list[Block]:
        """Check the tokens in the list.

        If the first token is a value or variable, the rest of the tokens will be ignored.
        If the first token is a function_id, then the next token can be a value,
            variable or named_arg, the rest have to be named_args.

        Raises:
            CodeBlockTokenError: If the content does not contain at least one token.
            CodeBlockTokenError: If the first token is a named argument.
            CodeBlockTokenError: If the second token is not a value or variable.
            CodeBlockTokenError: If a token is not a named argument after the second token.
        """
        if not tokens:
            raise CodeBlockTokenError("The content should contain at least one token.")
        for index, token in enumerate(tokens):
            if index == 0 and token.type == BlockTypes.NAMED_ARG:
                raise CodeBlockTokenError(
                    f"The first token needs to be a function_id, value or variable, got: {token.type}"
                )
            if index == 0 and token.type in [BlockTypes.VALUE, BlockTypes.VARIABLE]:
                if len(tokens) > 1:
                    logger.warning(
                        "The first token is a value or variable, but there are more tokens in the content, \
these will be ignored."
                    )
                return [token]
            if index == 1 and token.type not in VALID_ARG_TYPES:
                raise CodeBlockTokenError(
                    f"Unexpected type for the second token type, should be variable, value or named_arg: {token.type}"
                )
            if index > 1 and token.type != BlockTypes.NAMED_ARG:
                raise CodeBlockTokenError(
                    f"Every argument for the function after the first has to be a named arg, instead: {token.type}"
                )
        return tokens

    async def render_code(self, kernel: "Kernel", arguments: "KernelArguments") -> str:
        """Render the code block.

        If the first token is a function_id, it will call the function from the plugin collection.
        Otherwise, it is a value or variable and those are then rendered directly.
        """
        logger.debug(f"Rendering code: `{self.content}`")
        if isinstance(self.tokens[0], FunctionIdBlock):
            return await self._render_function_call(kernel, arguments)
        # validated that if the first token is not a function_id, it is a value or variable
        return self.tokens[0].render(kernel, arguments)  # type: ignore

    async def _render_function_call(
        self, kernel: "Kernel", arguments: "KernelArguments"
    ):
        if not isinstance(self.tokens[0], FunctionIdBlock):
            raise CodeBlockRenderException("The first token should be a function_id")
        function_block: FunctionIdBlock = self.tokens[0]
        try:
            function = kernel.get_function(
                function_block.plugin_name, function_block.function_name
            )
        except (KernelFunctionNotFoundError, KernelPluginNotFoundError) as exc:
            error_msg = f"Function `{function_block.content}` not found"
            logger.error(error_msg)
            raise CodeBlockRenderException(error_msg) from exc
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes

        arguments_clone = copy(arguments)
        if len(self.tokens) > 1:
            arguments_clone = self._enrich_function_arguments(
                kernel, arguments_clone, function.metadata
            )
        try:
            result = await function.invoke(kernel, arguments_clone)
        except Exception as exc:
            error_msg = f"Error invoking function `{function_block.content}`"
            logger.error(error_msg)
            raise CodeBlockRenderException(error_msg) from exc
        return str(result) if result else ""

    def _enrich_function_arguments(
        self,
        kernel: "Kernel",
        arguments: "KernelArguments",
        function_metadata: KernelFunctionMetadata,
    ) -> "KernelArguments":
        if not function_metadata.parameters:
            raise CodeBlockRenderException(
                f"Function {function_metadata.plugin_name}.{function_metadata.name} does not take any arguments "
                f"but it is being called in the template with {len(self.tokens) - 1} arguments."
            )
        for index, token in enumerate(self.tokens[1:], start=1):
            logger.debug(f"Parsing variable/value: `{self.tokens[1].content}`")
            rendered_value = token.render(kernel, arguments)  # type: ignore
            if not isinstance(token, NamedArgBlock) and index == 1:
                arguments[function_metadata.parameters[0].name] = rendered_value
                continue
            arguments[token.name] = rendered_value  # type: ignore

        return arguments
from logging import Logger
from re import match as regex_match
from typing import Optional, Tuple

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
<<<<<<< Updated upstream
=======
<<<<<<< main
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import Field, field_validator, model_validator

from semantic_kernel.exceptions import CodeBlockRenderException, CodeBlockTokenError
from semantic_kernel.exceptions.kernel_exceptions import (
    KernelFunctionNotFoundError,
    KernelPluginNotFoundError,
>>>>>>> origin/main
)
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
=======
from typing import TYPE_CHECKING, Any, ClassVar, List, Optional

from pydantic import Field, field_validator, model_validator

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection
>>>>>>> ms/small_fixes
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_errors import CodeBlockRenderError, CodeBlockTokenError
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
<<<<<<< head
from semantic_kernel.template_engine.blocks.var_block import VarBlock
from semantic_kernel.template_engine.template_exception import TemplateException
=======
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine.blocks.named_arg_block import NamedArgBlock
from semantic_kernel.template_engine.code_tokenizer import CodeTokenizer
>>>>>>> origin/main

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
<<<<<<< main
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

VALID_ARG_TYPES = [BlockTypes.VALUE, BlockTypes.VARIABLE, BlockTypes.NAMED_ARG]


class CodeBlock(Block):
<<<<<<< head
    _validated: bool = False

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
=======
    """Create a code block.

    A code block is a block that usually contains functions to be executed by the kernel.
    It consists of a list of tokens that can be either a function_id, value, a variable or a named argument.

    If the first token is not a function_id but a variable or value, the rest of the tokens will be ignored.
    Only the first argument for the function can be a variable or value, the rest of the tokens have be named arguments.

    Args:
        content: The content of the code block.
        tokens: The list of tokens that compose the code block, if empty, will be created by the CodeTokenizer.

    Raises:
        CodeBlockTokenError: If the content does not contain at least one token.
        CodeBlockTokenError: If the first token is a named argument.
        CodeBlockTokenError: If the second token is not a value or variable.
        CodeBlockTokenError: If a token is not a named argument after the second token.
        CodeBlockRenderError: If the plugin collection is not set in the kernel.
        CodeBlockRenderError: If the function is not found in the plugin collection.
        CodeBlockRenderError: If the function does not take any arguments, but it is being
            called in the template with arguments.
    """

    type: ClassVar[BlockTypes] = BlockTypes.CODE
    tokens: list[Block] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Any) -> Any:
        """Parse the content of the code block and tokenize it.

        If tokens are already present, skip the tokenizing.
        """
        if isinstance(fields, Block) or "tokens" in fields:
            return fields
        content = fields.get("content", "").strip()
        fields["tokens"] = CodeTokenizer.tokenize(content)
        return fields

    @field_validator("tokens", mode="after")
    def check_tokens(cls, tokens: list[Block]) -> list[Block]:
        """Check the tokens in the list.

        If the first token is a value or variable, the rest of the tokens will be ignored.
        If the first token is a function_id, then the next token can be a value,
            variable or named_arg, the rest have to be named_args.

        Raises:
            CodeBlockTokenError: If the content does not contain at least one token.
            CodeBlockTokenError: If the first token is a named argument.
            CodeBlockTokenError: If the second token is not a value or variable.
            CodeBlockTokenError: If a token is not a named argument after the second token.
        """
        if not tokens:
            raise CodeBlockTokenError("The content should contain at least one token.")
        for index, token in enumerate(tokens):
            if index == 0 and token.type == BlockTypes.NAMED_ARG:
                raise CodeBlockTokenError(
                    f"The first token needs to be a function_id, value or variable, got: {token.type}"
                )
            if index == 0 and token.type in [BlockTypes.VALUE, BlockTypes.VARIABLE]:
                if len(tokens) > 1:
                    logger.warning(
                        "The first token is a value or variable, but there are more tokens in the content, \
these will be ignored."
                    )
                return [token]
            if index == 1 and token.type not in VALID_ARG_TYPES:
                raise CodeBlockTokenError(
                    f"Unexpected type for the second token type, should be variable, value or named_arg: {token.type}"
                )
            if index > 1 and token.type != BlockTypes.NAMED_ARG:
                raise CodeBlockTokenError(
                    f"Every argument for the function after the first has to be a named arg, instead: {token.type}"
                )
        return tokens

    async def render_code(self, kernel: "Kernel", arguments: "KernelArguments") -> str:
        """Render the code block.

        If the first token is a function_id, it will call the function from the plugin collection.
        Otherwise, it is a value or variable and those are then rendered directly.
        """
        logger.debug(f"Rendering code: `{self.content}`")
        if isinstance(self.tokens[0], FunctionIdBlock):
            return await self._render_function_call(kernel, arguments)
        # validated that if the first token is not a function_id, it is a value or variable
        return self.tokens[0].render(kernel, arguments)  # type: ignore

    async def _render_function_call(
        self, kernel: "Kernel", arguments: "KernelArguments"
    ):
        if not isinstance(self.tokens[0], FunctionIdBlock):
            raise CodeBlockRenderException("The first token should be a function_id")
        function_block: FunctionIdBlock = self.tokens[0]
        try:
            function = kernel.get_function(
                function_block.plugin_name, function_block.function_name
            )
        except (KernelFunctionNotFoundError, KernelPluginNotFoundError) as exc:
            error_msg = f"Function `{function_block.content}` not found"
            logger.error(error_msg)
            raise CodeBlockRenderException(error_msg) from exc
>>>>>>> origin/main
=======
)
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.var_block import VarBlock
from semantic_kernel.template_engine.template_exception import TemplateException


class CodeBlock(Block):
    _validated: bool = False

=======
>>>>>>> Stashed changes

        arguments_clone = copy(arguments)
        if len(self.tokens) > 1:
            arguments_clone = self._enrich_function_arguments(
                kernel, arguments_clone, function.metadata
            )
        try:
            result = await function.invoke(kernel, arguments_clone)
        except Exception as exc:
            error_msg = f"Error invoking function `{function_block.content}`"
            logger.error(error_msg)
            raise CodeBlockRenderException(error_msg) from exc
        return str(result) if result else ""

    def _enrich_function_arguments(
        self,
        kernel: "Kernel",
        arguments: "KernelArguments",
        function_metadata: KernelFunctionMetadata,
    ) -> "KernelArguments":
        if not function_metadata.parameters:
            raise CodeBlockRenderException(
                f"Function {function_metadata.plugin_name}.{function_metadata.name} does not take any arguments "
                f"but it is being called in the template with {len(self.tokens) - 1} arguments."
            )
        for index, token in enumerate(self.tokens[1:], start=1):
            logger.debug(f"Parsing variable/value: `{self.tokens[1].content}`")
            rendered_value = token.render(kernel, arguments)  # type: ignore
            if not isinstance(token, NamedArgBlock) and index == 1:
                arguments[function_metadata.parameters[0].name] = rendered_value
                continue
            arguments[token.name] = rendered_value  # type: ignore
<<<<<<< Updated upstream
<<<<<<< head

        return arguments
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

        return arguments
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

>>>>>>> origin/main
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
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes

        if error != "":
            self._log.error(error)
            return False, error
<<<<<<< Updated upstream
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

<<<<<<< Updated upstream
=======

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

>>>>>>> origin/main
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes

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
=======
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
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======

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
=======
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

VALID_ARG_TYPES = [BlockTypes.VALUE, BlockTypes.VARIABLE, BlockTypes.NAMED_ARG]


class CodeBlock(Block):
    """Create a code block.

    A code block is a block that usually contains functions to be executed by the kernel.
    It consists of a list of tokens that can be either a function_id, value, a variable or a named argument.

    If the first token is not a function_id but a variable or value, the rest of the tokens will be ignored.
    Only the first argument for the function can be a variable or value, the rest of the tokens have be named arguments.

    Args:
        content: The content of the code block.
        tokens: The list of tokens that compose the code block, if empty, will be created by the CodeTokenizer.

    Raises:
        CodeBlockTokenError: If the content does not contain at least one token.
        CodeBlockTokenError: If the first token is a named argument.
        CodeBlockTokenError: If the second token is not a value or variable.
        CodeBlockTokenError: If a token is not a named argument after the second token.
        CodeBlockRenderError: If the plugin collection is not set in the kernel.
        CodeBlockRenderError: If the function is not found in the plugin collection.
        CodeBlockRenderError: If the function does not take any arguments but it is being
            called in the template with arguments.
    """

    type: ClassVar[BlockTypes] = BlockTypes.CODE
    tokens: List[Block] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Any) -> Any:
        """Parse the content of the code block and tokenize it.

        If tokens are already present, skip the tokenizing.
        """
        if isinstance(fields, Block) or "tokens" in fields:
            return fields
        content = fields.get("content", "").strip()
        fields["tokens"] = CodeTokenizer.tokenize(content)
        return fields

    @field_validator("tokens", mode="after")
    def check_tokens(cls, tokens: List[Block]) -> List[Block]:
        """Check the tokens in the list.

        If the first token is a value or variable, the rest of the tokens will be ignored.
        If the first token is a function_id, then the next token can be a value,
            variable or named_arg, the rest have to be named_args.

        Raises:
            CodeBlockTokenError: If the content does not contain at least one token.
            CodeBlockTokenError: If the first token is a named argument.
            CodeBlockTokenError: If the second token is not a value or variable.
            CodeBlockTokenError: If a token is not a named argument after the second token.
        """
        if not tokens:
            raise CodeBlockTokenError("The content should contain at least one token.")
        for index, token in enumerate(tokens):
            if index == 0 and token.type == BlockTypes.NAMED_ARG:
                raise CodeBlockTokenError(
                    f"The first token needs to be a function_id, value or variable, got: {token.type}"
                )
            if index == 0 and token.type in [BlockTypes.VALUE, BlockTypes.VARIABLE]:
                if len(tokens) > 1:
                    logger.warning(
                        "The first token is a value or variable, but there are more tokens in the content, \
these will be ignored."
                    )
                return [token]
            if index == 1 and token.type not in VALID_ARG_TYPES:
                raise CodeBlockTokenError(
                    f"Unexpected type for the second token type, should be variable, value or named_arg: {token.type}"
                )
            if index > 1 and token.type != BlockTypes.NAMED_ARG:
                raise CodeBlockTokenError(
                    f"Every argument for the function after the first has to be a named arg, instead: {token.type}"
                )
        return tokens

    async def render_code(self, kernel: "Kernel", arguments: "KernelArguments") -> str:
        """Render the code block.

        If the first token is a function_id, it will call the function from the plugin collection.
        Otherwise it is a value or variable and those are then rendered directly.
        """
        logger.debug(f"Rendering code: `{self.content}`")
        if self.tokens[0].type == BlockTypes.FUNCTION_ID:
            return await self._render_function_call(kernel, arguments)
        # validated that if the first token is not a function_id, it is a value or variable
        return self.tokens[0].render(kernel, arguments)

    async def _render_function_call(self, kernel: "Kernel", arguments: "KernelArguments"):
        if not kernel.plugins:
            raise CodeBlockRenderError("Plugin collection not set in kernel")
        function_block = self.tokens[0]
        function = self._get_function_from_plugin_collection(kernel.plugins, function_block)
        if not function:
            error_msg = f"Function `{function_block.content}` not found"
            logger.error(error_msg)
            raise CodeBlockRenderError(error_msg)

        arguments_clone = copy(arguments)
        if len(self.tokens) > 1:
            arguments_clone = self._enrich_function_arguments(kernel, arguments_clone, function.metadata)

        result = await function.invoke(kernel, arguments_clone)
        if exc := result.metadata.get("error", None):
            raise CodeBlockRenderError(f"Error rendering function: {function.metadata} with error: {exc}") from exc

        return str(result) if result else ""

    def _enrich_function_arguments(
        self,
        kernel: "Kernel",
        arguments: "KernelArguments",
        function_metadata: KernelFunctionMetadata,
    ) -> "KernelArguments":
        if not function_metadata.parameters:
            raise CodeBlockRenderError(
                f"Function {function_metadata.plugin_name}.{function_metadata.name} does not take any arguments "
                f"but it is being called in the template with {len(self.tokens) - 1} arguments."
            )
        for index, token in enumerate(self.tokens[1:], start=1):
            logger.debug(f"Parsing variable/value: `{self.tokens[1].content}`")
            rendered_value = token.render(kernel, arguments)
            if token.type != BlockTypes.NAMED_ARG and index == 1:
                arguments[function_metadata.parameters[0].name] = rendered_value
                continue
            arguments[token.name] = rendered_value
>>>>>>> ms/small_fixes
>>>>>>> origin/main

        return arguments

<<<<<<< head
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
=======
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

VALID_ARG_TYPES = [BlockTypes.VALUE, BlockTypes.VARIABLE, BlockTypes.NAMED_ARG]


class CodeBlock(Block):
    """Create a code block.

    A code block is a block that usually contains functions to be executed by the kernel.
    It consists of a list of tokens that can be either a function_id, value, a variable or a named argument.

    If the first token is not a function_id but a variable or value, the rest of the tokens will be ignored.
    Only the first argument for the function can be a variable or value, the rest of the tokens have be named arguments.

    Args:
        content: The content of the code block.
        tokens: The list of tokens that compose the code block, if empty, will be created by the CodeTokenizer.

    Raises:
        CodeBlockTokenError: If the content does not contain at least one token.
        CodeBlockTokenError: If the first token is a named argument.
        CodeBlockTokenError: If the second token is not a value or variable.
        CodeBlockTokenError: If a token is not a named argument after the second token.
        CodeBlockRenderError: If the plugin collection is not set in the kernel.
        CodeBlockRenderError: If the function is not found in the plugin collection.
        CodeBlockRenderError: If the function does not take any arguments but it is being
            called in the template with arguments.
    """

    type: ClassVar[BlockTypes] = BlockTypes.CODE
    tokens: List[Block] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Any) -> Any:
        """Parse the content of the code block and tokenize it.

        If tokens are already present, skip the tokenizing.
        """
        if isinstance(fields, Block) or "tokens" in fields:
            return fields
        content = fields.get("content", "").strip()
        fields["tokens"] = CodeTokenizer.tokenize(content)
        return fields

    @field_validator("tokens", mode="after")
    def check_tokens(cls, tokens: List[Block]) -> List[Block]:
        """Check the tokens in the list.

        If the first token is a value or variable, the rest of the tokens will be ignored.
        If the first token is a function_id, then the next token can be a value,
            variable or named_arg, the rest have to be named_args.

        Raises:
            CodeBlockTokenError: If the content does not contain at least one token.
            CodeBlockTokenError: If the first token is a named argument.
            CodeBlockTokenError: If the second token is not a value or variable.
            CodeBlockTokenError: If a token is not a named argument after the second token.
        """
        if not tokens:
            raise CodeBlockTokenError("The content should contain at least one token.")
        for index, token in enumerate(tokens):
            if index == 0 and token.type == BlockTypes.NAMED_ARG:
                raise CodeBlockTokenError(
                    f"The first token needs to be a function_id, value or variable, got: {token.type}"
                )
            if index == 0 and token.type in [BlockTypes.VALUE, BlockTypes.VARIABLE]:
                if len(tokens) > 1:
                    logger.warning(
                        "The first token is a value or variable, but there are more tokens in the content, \
these will be ignored."
                    )
                return [token]
            if index == 1 and token.type not in VALID_ARG_TYPES:
                raise CodeBlockTokenError(
                    f"Unexpected type for the second token type, should be variable, value or named_arg: {token.type}"
                )
            if index > 1 and token.type != BlockTypes.NAMED_ARG:
                raise CodeBlockTokenError(
                    f"Every argument for the function after the first has to be a named arg, instead: {token.type}"
                )
        return tokens

    async def render_code(self, kernel: "Kernel", arguments: "KernelArguments") -> str:
        """Render the code block.

        If the first token is a function_id, it will call the function from the plugin collection.
        Otherwise it is a value or variable and those are then rendered directly.
        """
        logger.debug(f"Rendering code: `{self.content}`")
        if self.tokens[0].type == BlockTypes.FUNCTION_ID:
            return await self._render_function_call(kernel, arguments)
        # validated that if the first token is not a function_id, it is a value or variable
        return self.tokens[0].render(kernel, arguments)

    async def _render_function_call(self, kernel: "Kernel", arguments: "KernelArguments"):
        if not kernel.plugins:
            raise CodeBlockRenderError("Plugin collection not set in kernel")
        function_block = self.tokens[0]
        function = self._get_function_from_plugin_collection(kernel.plugins, function_block)
        if not function:
            error_msg = f"Function `{function_block.content}` not found"
            logger.error(error_msg)
            raise CodeBlockRenderError(error_msg)

        arguments_clone = copy(arguments)
        if len(self.tokens) > 1:
            arguments_clone = self._enrich_function_arguments(kernel, arguments_clone, function.metadata)

        result = await function.invoke(kernel, arguments_clone)
        if exc := result.metadata.get("error", None):
            raise CodeBlockRenderError(f"Error rendering function: {function.metadata} with error: {exc}") from exc

        return str(result) if result else ""

    def _enrich_function_arguments(
        self,
        kernel: "Kernel",
        arguments: "KernelArguments",
        function_metadata: KernelFunctionMetadata,
    ) -> "KernelArguments":
        if not function_metadata.parameters:
            raise CodeBlockRenderError(
                f"Function {function_metadata.plugin_name}.{function_metadata.name} does not take any arguments "
                f"but it is being called in the template with {len(self.tokens) - 1} arguments."
            )
        for index, token in enumerate(self.tokens[1:], start=1):
            logger.debug(f"Parsing variable/value: `{self.tokens[1].content}`")
            rendered_value = token.render(kernel, arguments)
            if token.type != BlockTypes.NAMED_ARG and index == 1:
                arguments[function_metadata.parameters[0].name] = rendered_value
                continue
            arguments[token.name] = rendered_value
>>>>>>> ms/small_fixes
>>>>>>> origin/main

        return arguments

<<<<<<< main
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

            if skills.has_semantic_function(skill_name, function_name):
                return True, skills.get_semantic_function(skill_name, function_name)

        return False, None
=======
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
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

            if skills.has_semantic_function(skill_name, function_name):
                return True, skills.get_semantic_function(skill_name, function_name)

        return False, None
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
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
    def _get_function_from_plugin_collection(
        self, plugins: KernelPluginCollection, function_block: FunctionIdBlock
    ) -> Optional["KernelFunction"]:
        """
        Get the function from the plugin collection

        Args:
            plugins: The plugin collection
            function_block: The function block that contains the function name

        Returns:
            The function if it exists, None otherwise.
        """
        if function_block.plugin_name is not None and len(function_block.plugin_name) > 0:
            return plugins[function_block.plugin_name][function_block.function_name]
        else:
            # We now require a plug-in name, but if one isn't set then we'll try to find the function
            for plugin in plugins:
                if function_block.function_name in plugin:
                    return plugin[function_block.function_name]

        return None
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
