# Copyright (c) Microsoft. All rights reserved.


import logging
from inspect import Parameter, Signature, isasyncgenfunction, isgeneratorfunction, signature
from typing import Any, Callable, Dict, Optional

NoneType = type(None)
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
    All of this is are stored in __kernel_function_parameters__.

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
        func.__kernel_function_parameters__ = [
            _parse_parameter(param) for param in func_sig.parameters.values() if param.name != "self"
        ]
        return_param_dict = {}
        if func_sig.return_annotation != Signature.empty:
            return_param_dict = _parse_annotation(func_sig.return_annotation)
        func.__kernel_function_return_type__ = return_param_dict.get("type_", "None")
        func.__kernel_function_return_description__ = return_param_dict.get("description", "")
        func.__kernel_function_return_required__ = return_param_dict.get("is_required", False)
        return func

    return decorator


def _parse_parameter(param: Parameter) -> Dict[str, Any]:
    logger.debug(f"Parsing param: {param}")
    ret = {}
    if param != Parameter.empty:
        ret = _parse_annotation(param.annotation)
    ret["name"] = param.name
    if param.default != Parameter.empty:
        ret["default_value"] = param.default
    return ret


def _parse_annotation(annotation: Parameter) -> Dict[str, Any]:
    logger.debug(f"Parsing annotation: {annotation}")
    if annotation == Signature.empty:
        return {"type_": "Any", "is_required": True}
    if isinstance(annotation, str):
        return {"type_": annotation, "is_required": True}
    logger.debug(f"{annotation=}")
    ret = _parse_internal_annotation(annotation, True)
    if hasattr(annotation, "__metadata__") and annotation.__metadata__:
        ret["description"] = annotation.__metadata__[0]
    return ret


def _parse_internal_annotation(annotation: Parameter, required: bool) -> Dict[str, Any]:
    logger.debug(f"Internal {annotation=}")
    if hasattr(annotation, "__forward_arg__"):
        return {"type_": annotation.__forward_arg__, "is_required": required}
    if getattr(annotation, "__name__", None) == "Optional":
        required = False
    if hasattr(annotation, "__args__"):
        results = [_parse_internal_annotation(arg, required) for arg in annotation.__args__]
        type_objects = [
            result["type_object"]
            for result in results
            if "type_object" in result and result["type_object"] is not NoneType
        ]
        str_results = [result["type_"] for result in results]
        if "NoneType" in str_results:
            str_results.remove("NoneType")
            required = False
        else:
            required = not (any(not result["is_required"] for result in results))
        ret = {"type_": ", ".join(str_results), "is_required": required}
        if type_objects and len(type_objects) == 1:
            ret["type_object"] = type_objects[0]
        return ret
    return {
        "type_": getattr(annotation, "__name__", ""),
        "type_object": annotation,
        "is_required": required,
    }
