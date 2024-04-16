# # Copyright (c) Microsoft. All rights reserved.
# from __future__ import annotations

# from semantic_kernel.hooks.function.function_hook_context_base import FunctionHookContextBase


# class PreFunctionInvokeContext(FunctionHookContextBase):
#     """Pre Function Invoke Context.

#     Receives relevant parts of the the execution, before the function is executed.
#     When a handler changes the arguments in the invoking event,
#     the whole new arguments are used, they are not updated, but replaced,
#     make sure to use the update_arguments function, since that also raises the flag that the arguments were updated.

#     Args:
#         function (KernelFunction): The function that is being executed.
#         arguments (KernelArguments): The arguments that are being passed to the function.
#         metadata (Dict[str, Any]): The metadata of the function that is being executed.

#     Flags:
#         updated_arguments (bool): Whether the arguments were updated, default False.
#         is_cancel_requested (bool): Whether the function execution has to be canceled, default False.

#     Methods:
#         cancel(cancel_reason: str | None): Sets the is_cancel_requested flag to True and stores the cancel_reason.
#         update_arguments: Updates the arguments and raises the updated_arguments flag.

#     """

#     pass
