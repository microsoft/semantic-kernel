# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from pydantic import Field

from semantic_kernel.hooks.function.function_hook_context_base import FunctionHookContextBase


class PreFunctionInvokeContext(FunctionHookContextBase):
    """Pre Function Invoke Context.

    Receives relevant parts of the the execution, before the function is executed.
    When a handler changes the arguments in the invoking event,
    the whole new arguments are used, they are not updated, but replaced,
    make sure to use the update_arguments function, since that also raises the flag that the arguments were updated.

    Args:
        function (KernelFunction): The function that is being executed.
        arguments (KernelArguments): The arguments that are being passed to the function.
        metadata (Dict[str, Any]): The metadata of the function that is being executed.

    Flags:
        updated_arguments (bool): Whether the arguments were updated, default False.
        is_cancel_requested (bool): Whether the function execution has to be canceled, default False.
        is_skip_requested (bool): Whether the function execution has to be skipped, default False.

    Methods:
        cancel: Sets the is_cancel_requested flag to True.
        update_arguments: Updates the arguments and raises the updated_arguments flag.
        skip: Sets the is_skip_requested flag to True.

    """

    is_skip_requested: bool = Field(default=False, init_var=False)

    def skip(self):
        self.is_skip_requested = True
