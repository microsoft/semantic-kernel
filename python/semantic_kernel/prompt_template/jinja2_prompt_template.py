# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from jinja2 import BaseLoader, TemplateError
from jinja2.sandbox import ImmutableSandboxedEnvironment
from pydantic import PrivateAttr, field_validator

from semantic_kernel.exceptions import Jinja2TemplateRenderException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.const import JINJA2_TEMPLATE_FORMAT_NAME
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.prompt_template.utils import JINJA2_SYSTEM_HELPERS
from semantic_kernel.prompt_template.utils.template_function_helpers import create_template_helper_from_function

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class Jinja2PromptTemplate(PromptTemplateBase):
    """Creates and renders Jinja2 prompt templates to text.

    Jinja2 templates support advanced features such as variable substitution, control structures,
    and inheritance, making it possible to dynamically generate text based on input arguments
    and predefined functions. This class leverages Jinja2's flexibility to render prompts that
    can include conditional logic, loops, and functions, based on the provided template configuration
    and arguments.

    Note that the fully qualified function name (in the form of "plugin-function") is not allowed
    in Jinja2 because of the hyphen. Therefore, the function name is replaced with an underscore,
    which are allowed in Python function names.

    Args:
        prompt_template_config (PromptTemplateConfig): The configuration object for the prompt template.
            This should specify the template format as 'jinja2' and include any necessary
            configuration details required for rendering the template.
        allow_dangerously_set_content (bool = False): Allow content without encoding throughout, this overrides
            the same settings in the prompt template config and input variables.
            This reverts the behavior to unencoded input.

    Raises:
        ValueError: If the template format specified in the configuration is not 'jinja2'.
        Jinja2TemplateSyntaxError: If there is a syntax error in the Jinja2 template.
    """

    _env: ImmutableSandboxedEnvironment | None = PrivateAttr()

    @field_validator("prompt_template_config")
    @classmethod
    def validate_template_format(cls, v: "PromptTemplateConfig") -> "PromptTemplateConfig":
        """Validate the template format."""
        if v.template_format != JINJA2_TEMPLATE_FORMAT_NAME:
            raise ValueError(f"Invalid prompt template format: {v.template_format}. Expected: jinja2")
        return v

    def model_post_init(self, _: Any) -> None:
        """Post init model."""
        if not self.prompt_template_config.template:
            self._env = None
            return
        self._env = ImmutableSandboxedEnvironment(loader=BaseLoader(), enable_async=True)

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
        if not self._env:
            return ""
        if arguments is None:
            arguments = KernelArguments()

        arguments = self._get_trusted_arguments(arguments)
        allow_unsafe_function_output = self._get_allow_dangerously_set_function_output()
        helpers: dict[str, Callable[..., Any]] = {}
        helpers.update(JINJA2_SYSTEM_HELPERS)
        for plugin in kernel.plugins.values():
            helpers.update({
                function.fully_qualified_name.replace("-", "_"): create_template_helper_from_function(
                    function,
                    kernel,
                    arguments,
                    self.prompt_template_config.template_format,
                    allow_unsafe_function_output,
                    enable_async=True,
                )
                for function in plugin
            })
        if self.prompt_template_config.template is None:
            raise Jinja2TemplateRenderException("Error rendering template, template is None")
        try:
            template = self._env.from_string(self.prompt_template_config.template, globals=helpers)
            return await template.render_async(**arguments)
        except TemplateError as exc:
            logger.error(
                f"Error rendering prompt template: {self.prompt_template_config.template} with arguments: {arguments}"
            )
            raise Jinja2TemplateRenderException(
                f"Error rendering prompt template: {self.prompt_template_config.template} with "
                f"arguments: {arguments}: error: {exc}"
            ) from exc
