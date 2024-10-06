# Copyright (c) Microsoft. All rights reserved.

from pydantic import Field

from semantic_kernel.events.kernel_events_args import KernelEventArgs


class FunctionInvokingEventArgs(KernelEventArgs):
    """Function Invoking Event Args.

    Receives relevant parts of the the execution, either before (invoking) the function is executed.
    When a handler changes the arguments in the invoking event,
    the new arguments are passed to the invoked event,
    make sure to use the update_arguments function, since that also raises the flag that the arguments were updated.

    Args:
        kernel_function_metadata (FunctionView): The function that is being executed.
        kernel_function_metadata (KernelFunctionMetadata): The function that is being executed.
        arguments (KernelArguments): The arguments that are being passed to the function.

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
