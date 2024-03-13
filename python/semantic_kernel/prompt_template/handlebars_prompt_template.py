# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, Optional

import nest_asyncio
from pybars import Compiler, PybarsError
from pydantic import PrivateAttr

from semantic_kernel.exceptions import HandlebarsTemplateRenderException, HandlebarsTemplateSyntaxError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.handlebars import HANDLEBAR_SYSTEM_HELPERS, create_helper_from_function
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class HandlebarsPromptTemplate(PromptTemplateBase):
    _template_compiler: Any = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        if not self.prompt_template_config.template:
            self._template_compiler = None
            return
        compiler = Compiler()
        try:
            self._template_compiler = compiler.compile(self.prompt_template_config.template)
        except PybarsError as e:
            logger.error(f"Invalid handlebars template: {self.prompt_template_config.template}")
            raise HandlebarsTemplateSyntaxError(
                f"Invalid handlebars template: {self.prompt_template_config.template}"
            ) from e
        nest_asyncio.apply()

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
        if not self._template_compiler:
            return ""
        if not arguments:
            arguments = KernelArguments()
        helpers = {}
        for plugin in kernel.plugins:
            helpers.update(
                {
                    function.fully_qualified_name: create_helper_from_function(function, kernel, arguments)
                    for function in plugin.functions.values()
                }
            )
        helpers.update(HANDLEBAR_SYSTEM_HELPERS)
        try:
            return self._template_compiler(arguments, helpers=helpers)
        except PybarsError as exc:
            logger.error(
                f"Error rendering prompt template: {self.prompt_template_config.template} with arguments: {arguments}"
            )
            raise HandlebarsTemplateRenderException(
                f"Error rendering prompt template: {self.prompt_template_config.template} with arguments: {arguments}: error: {exc}"
            ) from exc
