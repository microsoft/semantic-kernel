# Copyright (c) Microsoft. All rights reserved.


import logging
from inspect import Parameter, Signature, isasyncgenfunction, isgeneratorfunction, signature
from typing import Callable, Optional, Tuple

logger = logging.getLogger(__name__)


def kernel_function(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
):
    """
    Decorator for kernel functions.

    This decorator is used to mark a function as a kernel function. It also provides metadata for the function.
    The name and description can be left empty, and then the function name and docstring will be used.

    The parameters are parsed from the function signature, use typing.Annotated to provide a description for the
    parameter, in python 3.8, use typing_extensions.Annotated.

    To parse the type, first it checks if the parameter is annotated, and get's the description from there.
    After that it checks recursively until it reaches the lowest level, and it combines
    the types into a single comma-separated string, a forwardRef is also supported.
    All of this is are stored in __kernel_function_context_parameters__.

    The return type and description are parsed from the function signature,
    and that is stored in __kernel_function_return_type__, __kernel_function_return_description__
    and __kernel_function_return_required__.

    It also checks if the function is a streaming type (generator or iterable, async or not),
    and that is stored as a bool in __kernel_function_streaming__.

    Args:
        name (Optional[str]) -- The name of the function, if not supplied, the function name will be used.
        description (Optional[str]) -- The description of the function,
            if not supplied, the function docstring will be used, can be None.

    """

    def decorator(func: Callable):
        func.__kernel_function__ = True
        func.__kernel_function_description__ = description or func.__doc__
        func.__kernel_function_name__ = name or func.__name__
        func.__kernel_function_streaming__ = isasyncgenfunction(func) or isgeneratorfunction(func)
        logger.debug(f"Parsing decorator for function: {func.__kernel_function_name__}")

        func_sig = signature(func)
        logger.debug(f"{func_sig=}")
        func.__kernel_function_context_parameters__ = [
            _parse_parameter(param) for param in func_sig.parameters.values() if param.name != "self"
        ]

        if func_sig.return_annotation != Signature.empty:
            return_description, return_type, return_required = _parse_annotation(func_sig.return_annotation)
        else:
            return_description, return_type, return_required = "", "None", False
        func.__kernel_function_return_type__ = return_type
        func.__kernel_function_return_description__ = return_description
        func.__kernel_function_return_required__ = return_required
        return func

    return decorator


def _parse_parameter(param: Parameter):
    logger.debug(f"Parsing param: {param}")
    param_description = ""
    type_ = "str"
    required = True
    if param != Parameter.empty:
        param_description, type_, required = _parse_annotation(param.annotation)
    logger.debug(f"{param_description=}, {type_=}, {required=}")
    return {
        "name": param.name,
        "description": param_description,
        "default_value": param.default if param.default != Parameter.empty else None,
        "type": type_,
        "required": required,
    }


def _parse_annotation(annotation: Parameter) -> Tuple[str, str, bool]:
    logger.debug(f"Parsing annotation: {annotation}")
    if isinstance(annotation, str):
        return "", annotation, True
    logger.debug(f"{annotation=}")
    description = ""
    if hasattr(annotation, "__metadata__") and annotation.__metadata__:
        description = annotation.__metadata__[0]
    return (description, *_parse_internal_annotation(annotation, True))


def _parse_internal_annotation(annotation: Parameter, required: bool) -> Tuple[str, bool]:
    logger.debug(f"Internal {annotation=}")
    logger.debug(f"{annotation=}")
    if hasattr(annotation, "__forward_arg__"):
        return annotation.__forward_arg__, required
    if getattr(annotation, "__name__", None) == "Optional":
        required = False
    if hasattr(annotation, "__args__"):
        results = [_parse_internal_annotation(arg, required) for arg in annotation.__args__]
        str_results = [result[0] for result in results]
        if "NoneType" in str_results:
            str_results.remove("NoneType")
            required = False
        else:
            required = not (any(not result[1] for result in results))
        return ", ".join(str_results), required
    return getattr(annotation, "__name__", ""), required
