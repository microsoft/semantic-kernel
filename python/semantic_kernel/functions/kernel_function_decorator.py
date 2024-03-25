# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import logging
import sys
from functools import wraps
from inspect import Parameter, Signature, isasyncgenfunction, isgeneratorfunction
from typing import Any, Callable

if sys.version_info < (3, 10):
    from get_annotations import get_annotations
else:
    from inspect import get_annotations

NoneType = type(None)
logger = logging.getLogger(__name__)


def kernel_function(
    func: Callable[..., Any] | None = None,
    name: str | None = None,
    description: str | None = None,
) -> Callable[..., Any]:
    """
    Decorator for kernel functions, can be used directly as @kernel_function
    or with parameters @kernel_function(name='function', description='I am a function.').

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
        name (str | None) -- The name of the function, if not supplied, the function name will be used.
        description (str | None) -- The description of the function,
            if not supplied, the function docstring will be used, can be None.

    """

    @wraps(func)
    def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        func.__kernel_function__ = True
        func.__kernel_function_description__ = description or func.__doc__
        func.__kernel_function_name__ = name or func.__name__
        func.__kernel_function_streaming__ = isasyncgenfunction(func) or isgeneratorfunction(func)
        logger.debug(f"Parsing decorator for function: {func.__kernel_function_name__}")
        try:
            annotations = get_annotations(func, eval_str=True)
        except Exception as ex:
            logger.error(f"Failed to get annotations for function {func.__name__}: {ex}")
            annotations = {}
        # if sys.version_info >= (3, 10):
        #     func_sig = signature(func, eval_str=True)
        # else:
        #     # func_sig = signature(func)
        #     param_types: dict[str, Any] = get_annotations(func, eval_str=True)
        #     new_parameters: list[Parameter] = []
        #     if "self" in func_sig.parameters:
        #         new_parameters.append(func_sig.parameters["self"])
        #     for p_name, param in param_types.items():
        #         if p_name not in func_sig.parameters:
        #             continue
        #         orig_param = func_sig.parameters[p_name]
        #         new_parameters.append(
        #             Parameter(name=p_name, kind=orig_param.kind, annotation=param, default=orig_param.default)
        #         )
        #     func_sig.replace(
        #         parameters=new_parameters,
        #         return_annotation=param_types.get("return", func_sig.return_annotation),
        #     )

        logger.debug(f"{annotations=}")
        func.__kernel_function_parameters__ = [_parse_parameter(name, param) for name, param in annotations.items()]
        return_param_dict = {}
        if not annotations.get("return", None):
            return_param_dict = _parse_annotation(annotations.get("return"))
        func.__kernel_function_return_type__ = return_param_dict.get("type_", "None")
        func.__kernel_function_return_description__ = return_param_dict.get("description", "")
        func.__kernel_function_return_required__ = return_param_dict.get("is_required", False)
        return func

    if func:
        return decorator(func)
    return decorator


def _parse_parameter(name: str, param: Parameter) -> dict[str, Any]:
    logger.debug(f"Parsing param: {name}")
    logger.debug(f"Parsing annotation: {param}")
    ret = {"name": name}
    if not isinstance(param, str):
        if hasattr(param, "annotation"):
            ret = _parse_annotation(param.annotation)
        if hasattr(param, "default"):
            ret["default_value"] = param.default
    else:
        ret["type_"] = param
        ret["is_required"] = True
    return ret


def _parse_annotation(annotation: Parameter) -> dict[str, Any]:
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


def _parse_internal_annotation(annotation: Parameter, required: bool) -> dict[str, Any]:
    logger.debug(f"Internal {annotation=}")
    if hasattr(annotation, "__forward_arg__"):
        return {"type_": annotation.__forward_arg__, "is_required": required}
    if getattr(annotation, "__name__", None) == "Optional":
        required = False
    if hasattr(annotation, "__args__"):
        if getattr(annotation, "__name__", "").lower() in ["list", "dict"]:
            return {
                "type_": f"{annotation.__name__}[{', '.join([_parse_internal_annotation(arg, required)['type_'] for arg in annotation.__args__])}]",  # noqa: E501
                "is_required": required,
            }
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
