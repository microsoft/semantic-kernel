# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, Optional

from jinja2 import BaseLoader, Environment, TemplateError
from pydantic import PrivateAttr, field_validator

from semantic_kernel.exceptions import Jinja2TemplateRenderException, Jinja2TemplateSyntaxError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.const import JINJA2_TEMPLATE_FORMAT_NAME
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.prompt_template.utils import JINJA2_SYSTEM_HELPERS, create_template_helper_from_function

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class Jinja2PromptTemplate(PromptTemplateBase):
    """
    Creates and renders Jinja2 prompt templates to text.

    Jinja2 templates support advanced features such as variable substitution, control structures,
    and inheritance, making it possible to dynamically generate text based on input arguments
    and predefined functions. This class leverages Jinja2's flexibility to render prompts that
    can include conditional logic, loops, and functions, based on the provided template configuration
    and arguments.

    Note that the fully qualified function name (in the form of "plugin-function") is not allowed
    in Jinja2 because of the hyphen. Therefore, the function name is replaced with an underscore,
    which are allowed in Python function names.

    Args:
        template_config (PromptTemplateConfig): The configuration object for the prompt template.
            This should specify the template format as 'jinja2' and include any necessary
            configuration details required for rendering the template.

    Raises:
        ValueError: If the template format specified in the configuration is not 'jinja2'.
        Jinja2TemplateSyntaxError: If there is a syntax error in the Jinja2 template.
    """

    _env: Environment = PrivateAttr()

    @field_validator("prompt_template_config")
    @classmethod
    def validate_template_format(cls, v: "PromptTemplateConfig") -> "PromptTemplateConfig":
        if v.template_format != JINJA2_TEMPLATE_FORMAT_NAME:
            raise ValueError(f"Invalid prompt template format: {v.template_format}. Expected: jinja2")
        return v

    def model_post_init(self, __context: Any) -> None:
        if not self.prompt_template_config.template:
            self._env = None
            return
        try:
            self._env = Environment(loader=BaseLoader())
        except TemplateError as e:
            logger.error(f"Invalid jinja2 template: {self.prompt_template_config.template}")
            raise Jinja2TemplateSyntaxError(f"Invalid jinja2 template: {self.prompt_template_config.template}") from e

    async def render(self, kernel: "Kernel", arguments: Optional["KernelArguments"] = None) -> str:
        """
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
        if not arguments:
            arguments = KernelArguments()
        helpers = {}
        helpers.update(JINJA2_SYSTEM_HELPERS)
        for plugin in kernel.plugins:
            helpers.update(
                {
                    function.fully_qualified_name.replace("-", "_"): create_template_helper_from_function(
                        function,
                        kernel,
                        arguments,
                        self.prompt_template_config.template_format,
                    )
                    for function in plugin.functions.values()
                }
            )
        try:
            template = self._env.from_string(self.prompt_template_config.template, globals=helpers)
            return template.render(**arguments)
        except TemplateError as exc:
            logger.error(
                f"Error rendering prompt template: {self.prompt_template_config.template} with arguments: {arguments}"
            )
            raise Jinja2TemplateRenderException(
                f"Error rendering prompt template: {self.prompt_template_config.template} with "
                f"arguments: {arguments}: error: {exc}"
            ) from exc
