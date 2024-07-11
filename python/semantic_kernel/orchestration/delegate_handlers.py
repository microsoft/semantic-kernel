# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.orchestration.delegate_types import DelegateTypes
from semantic_kernel.sk_pydantic import PydanticField


def _handles(delegate_type):
    def decorator(function):
        function._delegate_type = delegate_type
        return function

    return decorator


class DelegateHandlers(PydanticField):
    @staticmethod
    @_handles(DelegateTypes.Void)
    async def handle_void(function, context):
        function()
        return context

    @staticmethod
    @_handles(DelegateTypes.OutString)
    async def handle_out_string(function, context):
        context.variables.update(function())
        return context

    @staticmethod
    @_handles(DelegateTypes.OutTaskString)
    async def handle_out_task_string(function, context):
        context.variables.update(await function())
        return context

    @staticmethod
    @_handles(DelegateTypes.InSKContext)
    async def handle_in_sk_context(function, context):
        function(context)
        return context

    @staticmethod
    @_handles(DelegateTypes.InSKContextOutString)
    async def handle_in_sk_context_out_string(function, context):
        context.variables.update(function(context))
        return context

    @staticmethod
    @_handles(DelegateTypes.InSKContextOutTaskString)
    async def handle_in_sk_context_out_task_string(function, context):
        context.variables.update(await function(context))
        return context

    @staticmethod
    @_handles(DelegateTypes.ContextSwitchInSKContextOutTaskSKContext)
    async def handle_context_switch_in_sk_context_out_task_sk_context(
        function, context
    ):
        # Note: Context Switching: allows the function to replace with a
        # new context, e.g. to branch execution path
        context = await function(context)
        return context

    @staticmethod
    @_handles(DelegateTypes.InString)
    async def handle_in_string(function, context):
        function(context.variables.input)
        return context

    @staticmethod
    @_handles(DelegateTypes.InStringOutString)
    async def handle_in_string_out_string(function, context):
        context.variables.update(function(context.variables.input))
        return context

    @staticmethod
    @_handles(DelegateTypes.InStringOutTaskString)
    async def handle_in_string_out_task_string(function, context):
        context.variables.update(await function(context.variables.input))
        return context

    @staticmethod
    @_handles(DelegateTypes.InStringAndContext)
    async def handle_in_string_and_context(function, context):
        function(context.variables.input, context)
        return context

    @staticmethod
    @_handles(DelegateTypes.InStringAndContextOutString)
    async def handle_in_string_and_context_out_string(function, context):
        context.variables.update(function(context.variables.input, context))
        return context

    @staticmethod
    @_handles(DelegateTypes.InStringAndContextOutTaskString)
    async def handle_in_string_and_context_out_task_string(function, context):
        context.variables.update(await function(context.variables.input, context))
        return context

    @staticmethod
    @_handles(DelegateTypes.ContextSwitchInStringAndContextOutTaskContext)
    async def handle_context_switch_in_string_and_context_out_task_context(
        function, context
    ):
        # Note: Context Switching: allows the function to replace with a
        # new context, e.g. to branch execution path
        context = await function(context.variables.input, context)
        return context

    @staticmethod
    @_handles(DelegateTypes.InStringOutTask)
    async def handle_in_string_out_task(function, context):
        await function(context.variables.input)
        return context

    @staticmethod
    @_handles(DelegateTypes.InContextOutTask)
    async def handle_in_context_out_task(function, context):
        await function(context)
        return context

    @staticmethod
    @_handles(DelegateTypes.InStringAndContextOutTask)
    async def handle_in_string_and_context_out_task(function, context):
        await function(context.variables.input, context)
        return context

    @staticmethod
    @_handles(DelegateTypes.OutTask)
    async def handle_out_task(function, context):
        await function()
        return context

    @staticmethod
    @_handles(DelegateTypes.Unknown)
    async def handle_unknown(function, context):
        raise KernelException(
            KernelException.ErrorCodes.FunctionTypeNotSupported,
            "Invalid function type detected, unable to execute.",
        )

    @staticmethod
    def get_handler(delegate_type):
        for name, value in DelegateHandlers.__dict__.items():
            wrapped = getattr(value, "__wrapped__", getattr(value, "__func__", None))
            if name.startswith("handle_") and hasattr(wrapped, "_delegate_type"):
                if wrapped._delegate_type == delegate_type:
                    return value

        return DelegateHandlers.handle_unknown
