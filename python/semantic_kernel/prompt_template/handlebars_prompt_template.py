# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from pybars import Compiler, PybarsError
from pydantic import PrivateAttr, field_validator

from semantic_kernel.exceptions import HandlebarsTemplateRenderException, HandlebarsTemplateSyntaxError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.const import HANDLEBARS_TEMPLATE_FORMAT_NAME
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.utils import HANDLEBAR_SYSTEM_HELPERS, create_template_helper_from_function

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

logger: logging.Logger = logging.getLogger(__name__)


class HandlebarsPromptTemplate(PromptTemplateBase):
    """Create a Handlebars prompt template.

    Handlebars are parsed as a whole and therefore do not have variables that can be extracted,
    also with handlebars there is no distinction in syntax between a variable and a value,
    a value that is encountered is tried to resolve with the arguments and the functions,
    if not found, the literal value is returned.

    Args:
        prompt_template_config (PromptTemplateConfig): The prompt template configuration
            This is checked if the template format is 'handlebars'
        allow_dangerously_set_content (bool = False): Allow content without encoding throughout, this overrides
            the same settings in the prompt template config and input variables.
            This reverts the behavior to unencoded input.

    Raises:
        ValueError: If the template format is not 'handlebars'
        HandlebarsTemplateSyntaxError: If the handlebars template has a syntax error
    """

    _template_compiler: Any = PrivateAttr()

    @field_validator("prompt_template_config")
    @classmethod
    def validate_template_format(cls, v: "PromptTemplateConfig") -> "PromptTemplateConfig":
        """Validate the template format."""
        if v.template_format != HANDLEBARS_TEMPLATE_FORMAT_NAME:
            raise ValueError(f"Invalid prompt template format: {v.template_format}. Expected: handlebars")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Post init model."""
        if not self.prompt_template_config.template:
            self._template_compiler = None
            return
        try:
            self._template_compiler = Compiler().compile(self.prompt_template_config.template)
        except PybarsError as e:
            logger.error(f"Invalid handlebars template: {self.prompt_template_config.template}")
            raise HandlebarsTemplateSyntaxError(
                f"Invalid handlebars template: {self.prompt_template_config.template}"
            ) from e

    async def render(self, kernel: "Kernel", arguments: "KernelArguments | None" = None) -> str:
        """Render the prompt template.

        Using the prompt template, replace the variables with their values
        and execute the functions replacing their reference with the
        function result.

        Args:
            kernel: The kernel instance
            arguments: The kernel arguments

        Returns:
            The prompt template ready to be used for an AI request
        """
        if not self._template_compiler:
            return ""
        if arguments is None:
            arguments = KernelArguments()

        arguments = self._get_trusted_arguments(arguments)
        allow_unsafe_function_output = self._get_allow_dangerously_set_function_output()
        helpers: dict[str, Callable[..., Any]] = {}
        for plugin in kernel.plugins.values():
            helpers.update({
                function.fully_qualified_name: create_template_helper_from_function(
                    function,
                    kernel,
                    arguments,
                    self.prompt_template_config.template_format,
                    allow_unsafe_function_output,
                )
                for function in plugin
            })
        helpers.update(HANDLEBAR_SYSTEM_HELPERS)

        try:
            return self._template_compiler(
                arguments,
                helpers=helpers,
            )
        except PybarsError as exc:
            logger.error(
                f"Error rendering prompt template: {self.prompt_template_config.template} with arguments: {arguments}"
            )
            raise HandlebarsTemplateRenderException(
                f"Error rendering prompt template: {self.prompt_template_config.template} "
                f"with arguments: {arguments}: error: {exc}"
            ) from exc
