# Copyright (c) Microsoft. All rights reserved.

from pydantic import Field

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel


class KernelEventArgs(KernelBaseModel):
    """Base class for Kernel Event args.

    Receives relevant parts of the the execution, either before (invoking) or after (invoked) the function is executed.
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

    Methods:
        cancel: Sets the is_cancel_requested flag to True.
        update_arguments: Updates the arguments and raises the updated_arguments flag.

    """

    kernel_function_metadata: KernelFunctionMetadata
    arguments: KernelArguments
    updated_arguments: bool = Field(default=False, init_var=False)
    is_cancel_requested: bool = Field(default=False, init_var=False)

    def cancel(self):
        self.is_cancel_requested = True

    def update_arguments(self, new_arguments: KernelArguments):
        self.arguments = new_arguments
        self.updated_arguments = True
