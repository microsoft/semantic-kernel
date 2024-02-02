# Copyright (c) Microsoft. All rights reserved.


from inspect import Parameter, signature
from typing import Callable, Tuple


def kernel_function(
    *,
    description: str = "",
    name: str = "",
):
    """
    Decorator for kernel functions.

    Args:
        description -- The description of the function
        name -- The name of the function
        input_description -- The description of the input
        input_default_value -- The default value of the input
    """

    def decorator(func: Callable):
        func.__kernel_function__ = True
        func.__kernel_function_description__ = description or func.__doc__ or ""
        func.__kernel_function_name__ = name or func.__name__
        func.__kernel_function_context_parameters__ = []
        func_sig = signature(func)
        for param in func_sig.parameters.values():
            if param.name != "self":
                func.__kernel_function_context_parameters__.append(_parse_parameter(param))
        if not func_sig.return_annotation:
            return_description, return_type, return_required, streaming = "", "None", False, False
        else:
            return_description, return_type, return_required, streaming = _parse_annotation(func_sig.return_annotation)
        func.__kernel_function_streaming__ = streaming
        func.__kernel_function_return_type__ = return_type
        func.__kernel_function_return_description__ = return_description
        func.__kernel_function_return_required__ = return_required
        return func

    return decorator


def _parse_parameter(param: Parameter):
    param_description, type_, required, _ = _parse_annotation(param.annotation)
    return {
        "name": param.name,
        "description": param_description,
        "default_value": param.default if param.default != Parameter.empty else None,
        "type": type_,
        "required": required,
    }


def _parse_annotation(annotation) -> Tuple[str, str, bool, bool]:
    if isinstance(annotation, str):
        return "", annotation, True, False
    if annotation.__name__ == "Annotated":
        description = annotation.__metadata__[0]
        type_annotation = annotation.__args__[0]
    else:
        description = ""
        type_annotation = annotation
    if type_annotation.__name__ == "Optional":
        type_annotation = type_annotation.__args__[0]
        required = False
    else:
        required = True
    if type_annotation.__name__ in [
        "AsyncIterable",
        "AsyncGenerator",
        "AsyncIterator",
        "Iterable",
        "Generator",
        "Iterator",
    ]:
        streaming = True
        type_annotation = type_annotation.__args__[0]
    else:
        streaming = False
    return description, type_annotation.__name__, required, streaming
