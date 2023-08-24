# Copyright (c) Microsoft. All rights reserved.

from inspect import Signature, iscoroutinefunction, signature
from typing import NoReturn

from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.orchestration.delegate_types import DelegateTypes
from semantic_kernel.sk_pydantic import PydanticField


def _infers(delegate_type):
    def decorator(function):
        function._delegate_type = delegate_type
        return function

    return decorator


def _is_annotation_of_type(annotation, type_to_match) -> bool:
    return (annotation is type_to_match) or (
        # Handle cases where the annotation is provided as a string to avoid circular imports
        # for example: `async def read_async(self, context: "SKContext"):` in file_io_skill.py
        isinstance(annotation, str)
        and annotation == type_to_match.__name__
    )


def _has_no_params(signature: Signature) -> bool:
    return len(signature.parameters) == 0


def _return_is_str(signature: Signature) -> bool:
    return signature.return_annotation is str


def _return_is_context(signature: Signature) -> bool:
    from semantic_kernel.orchestration.sk_context import SKContext

    return _is_annotation_of_type(signature.return_annotation, SKContext)


def _no_return(signature: Signature) -> bool:
    return signature.return_annotation is Signature.empty


def _has_first_param_with_type(
    signature: Signature, annotation, only: bool = True
) -> bool:
    if len(signature.parameters) < 1:
        return False
    if only and len(signature.parameters) != 1:
        return False

    first_param = list(signature.parameters.values())[0]
    return _is_annotation_of_type(first_param.annotation, annotation)


def _has_two_params_second_is_context(signature: Signature) -> bool:
    from semantic_kernel.orchestration.sk_context import SKContext

    if len(signature.parameters) < 2:
        return False
    second_param = list(signature.parameters.values())[1]
    return _is_annotation_of_type(second_param.annotation, SKContext)


def _first_param_is_str(signature: Signature, only: bool = True) -> bool:
    return _has_first_param_with_type(signature, str, only)


def _first_param_is_context(signature: Signature) -> bool:
    from semantic_kernel.orchestration.sk_context import SKContext

    return _has_first_param_with_type(signature, SKContext)


class DelegateInference(PydanticField):
    @staticmethod
    @_infers(DelegateTypes.Void)
    def infer_void(signature: Signature, awaitable: bool) -> bool:
        matches = _has_no_params(signature)
        matches = matches and _no_return(signature)
        matches = matches and not awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.OutString)
    def infer_out_string(signature: Signature, awaitable: bool) -> bool:
        matches = _has_no_params(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and not awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.OutTaskString)
    def infer_out_task_string(signature: Signature, awaitable: bool) -> bool:
        matches = _has_no_params(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InSKContext)
    def infer_in_sk_context(signature: Signature, awaitable: bool) -> bool:
        matches = _first_param_is_context(signature)
        matches = matches and _no_return(signature)
        matches = matches and not awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InSKContextOutString)
    def infer_in_sk_context_out_string(signature: Signature, awaitable: bool) -> bool:
        matches = _first_param_is_context(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and not awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InSKContextOutTaskString)
    def infer_in_sk_context_out_task_string(
        signature: Signature, awaitable: bool
    ) -> bool:
        matches = _first_param_is_context(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.ContextSwitchInSKContextOutTaskSKContext)
    def infer_context_switch_in_sk_context_out_task_sk_context(
        signature: Signature, awaitable: bool
    ) -> bool:
        matches = _first_param_is_context(signature)
        matches = matches and _return_is_context(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InString)
    def infer_in_string(signature: Signature, awaitable: bool) -> bool:
        matches = _first_param_is_str(signature)
        matches = matches and _no_return(signature)
        matches = matches and not awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringOutString)
    def infer_in_string_out_string(signature: Signature, awaitable: bool) -> bool:
        matches = _first_param_is_str(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and not awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringOutTaskString)
    def infer_in_string_out_task_string(signature: Signature, awaitable: bool) -> bool:
        matches = _first_param_is_str(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringAndContext)
    def infer_in_string_and_context(signature: Signature, awaitable: bool) -> bool:
        matches = _first_param_is_str(signature, only=False)
        matches = matches and _has_two_params_second_is_context(signature)
        matches = matches and _no_return(signature)
        matches = matches and not awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringAndContextOutString)
    def infer_in_string_and_context_out_string(
        signature: Signature, awaitable: bool
    ) -> bool:
        matches = _first_param_is_str(signature, only=False)
        matches = matches and _has_two_params_second_is_context(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and not awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringAndContextOutTaskString)
    def infer_in_string_and_context_out_task_string(
        signature: Signature, awaitable: bool
    ) -> bool:
        matches = _first_param_is_str(signature, only=False)
        matches = matches and _has_two_params_second_is_context(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.ContextSwitchInStringAndContextOutTaskContext)
    def infer_context_switch_in_string_and_context_out_task_context(
        signature: Signature, awaitable: bool
    ) -> bool:
        matches = _first_param_is_str(signature, only=False)
        matches = matches and _has_two_params_second_is_context(signature)
        matches = matches and _return_is_context(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringOutTask)
    def infer_in_string_out_task(signature: Signature, awaitable: bool) -> bool:
        matches = _first_param_is_str(signature)
        matches = matches and _no_return(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InContextOutTask)
    def infer_in_context_out_task(signature: Signature, awaitable: bool) -> bool:
        matches = _first_param_is_context(signature)
        matches = matches and _no_return(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringAndContextOutTask)
    def infer_in_string_and_context_out_task(
        signature: Signature, awaitable: bool
    ) -> bool:
        matches = _first_param_is_str(signature, only=False)
        matches = matches and _has_two_params_second_is_context(signature)
        matches = matches and _no_return(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.OutTask)
    def infer_out_task(signature: Signature, awaitable: bool) -> bool:
        matches = _has_no_params(signature)
        matches = matches and _no_return(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.Unknown)
    def infer_unknown(signature: Signature, awaitable: bool) -> NoReturn:
        raise KernelException(
            KernelException.ErrorCodes.FunctionTypeNotSupported,
            "Invalid function type detected, unable to infer DelegateType."
            + f" Function: {signature}",
        )

    @staticmethod
    def infer_delegate_type(function) -> DelegateTypes:
        # Get the function signature
        function_signature = signature(function)
        awaitable = iscoroutinefunction(function)

        for name, value in DelegateInference.__dict__.items():
            wrapped = getattr(value, "__wrapped__", getattr(value, "__func__", None))

            if name.startswith("infer_") and hasattr(wrapped, "_delegate_type"):
                # Get the delegate type
                if wrapped(function_signature, awaitable):
                    return wrapped._delegate_type

        return DelegateTypes.Unknown
