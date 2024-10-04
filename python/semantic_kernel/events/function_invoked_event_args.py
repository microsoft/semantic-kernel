# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from pydantic import Field

from semantic_kernel.events.kernel_events_args import KernelEventArgs
from semantic_kernel.functions.function_result import FunctionResult


class FunctionInvokedEventArgs(KernelEventArgs):
    """Function Invoked Event Args.

    Receives relevant parts of the the execution, after (invoked) the function is executed.
    When a handler changes the arguments in the invoking event,
    the new arguments are passed to the invoked event,
    make sure to use the update_arguments function, since that also raises the flag that the arguments were updated.

    If exception is not None, the function execution failed,
    if you want the execution of the pipeline to continue, you need to clear the exception.
    You can then also set the repeat flag to True, to repeat the function execution, possible with updated arguments.

    Args:
        kernel_function_metadata (FunctionView): The function that is being executed.
        kernel_function_metadata (KernelFunctionMetadata): The function that is being executed.
        arguments (KernelArguments): The arguments that are being passed to the function.
        function_result (FunctionResult): The result of the function execution.
        exception (Optional: Exception): The exception that was raised during the function execution.

    Flags:
        updated_arguments (bool): Whether the arguments were updated, default False.
        is_cancel_requested (bool): Whether the function execution has to be canceled, default False.
        is_repeat_requested (bool): Whether the function execution has to be repeated, default False.

    Methods:
        cancel: Sets the is_cancel_requested flag to True.
        update_arguments: Updates the arguments and raises the updated_arguments flag.
        repeat: Sets the is_repeat_requested flag to True.
    """

    function_result: Optional[FunctionResult] = None
    exception: Optional[Exception] = None
    is_repeat_requested: bool = Field(default=False, init_var=False)

    def repeat(self):
        self.is_repeat_requested = True
