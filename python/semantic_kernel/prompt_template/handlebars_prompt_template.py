# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, Optional

import pybars
from pybars import Compiler
from pydantic import PrivateAttr

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.handlebars.handlebars_functions import (
    _array,
    _camel_case,
    _concat,
    _double_close,
    _double_open,
    _equal,
    _get,
    _greater_than,
    _greater_than_or_equal,
    _json,
    _less_than,
    _less_than_or_equal,
    _message,
    _range,
    _set,
    create_func,
)
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class HandlebarsPromptTemplate(PromptTemplateBase):
    prompt_template_config: PromptTemplateConfig
    _template_compiler: Any = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        compiler = Compiler()
        pybars.debug = True
        self._template_compiler = compiler.compile(self.prompt_template_config.template)

    # def _add_if_missing(self, variable_name: str, seen: Optional[set] = None):
    # Convert variable_name to lower case to handle case-insensitivity
    # TODO: check inputvariables
    # if variable_name and variable_name.lower() not in seen:
    #     seen.add(variable_name.lower())
    #     self.prompt_template_config.input_variables.append(InputVariable(name=variable_name))

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
        if not arguments:
            arguments = KernelArguments()
        helpers = {
            "message": _message,
            "set": _set,
            "get": _get,
            "array": _array,
            "range": _range,
            "concat": _concat,
            "equal": _equal,
            "lessThan": _less_than,
            "greaterThan": _greater_than,
            "lessThanOrEqual": _less_than_or_equal,
            "greaterThanOrEqual": _greater_than_or_equal,
            "json": _json,
            "doubleOpen": _double_open,
            "doubleClose": _double_close,
            "camelCase": _camel_case,
        }

        for plugin in kernel.plugins:
            helpers.update({name: create_func(function, arguments) for name, function in plugin.functions.items()})
        return self._template_compiler(arguments, helpers=helpers)
