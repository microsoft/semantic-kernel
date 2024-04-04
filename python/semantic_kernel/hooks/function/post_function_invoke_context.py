# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

from pydantic import Field

from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.hooks.function.function_hook_context_base import FunctionHookContextBase


class PostFunctionInvokeContext(FunctionHookContextBase):
    """Post Function Invoke Context

    Receives relevant parts of the the execution, after the function is executed.
    When a handler changes the arguments
    the whole new arguments are used, they are not updated, but replaced,
    make sure to use the update_arguments function, since that also raises the flag that the arguments were updated.

    If exception is not None, the function execution failed,
    if you want the execution of the pipeline to continue, you need to clear the exception.
    You can then also set the repeat flag to True, to repeat the function execution, possible with updated arguments.

    Args:
        function (KernelFunction): The function that is being executed.
        arguments (KernelArguments): The arguments that are being passed to the function.
        function_result (FunctionResult): The result of the function execution.
        exception (Exception, optional): The exception that was raised during the function execution.
        metadata (Dict[str, Any]): The metadata of the function that is being executed.

    Flags:
        updated_arguments (bool): Whether the arguments were updated, default False.
        is_cancel_requested (bool): Whether the function execution has to be canceled, default False.
        is_repeat_requested (bool): Whether the function execution has to be repeated, default False.

    Methods:
        cancel: Sets the is_cancel_requested flag to True.
        update_arguments: Updates the arguments and sets the updated_arguments flag.
        repeat: Sets the is_repeat_requested flag to True.
    """

    function_result: FunctionResult | None = None
    exception: Exception | None = None
    is_repeat_requested: bool = Field(default=False, init_var=False)

    def repeat(self):
        self.is_repeat_requested = True
