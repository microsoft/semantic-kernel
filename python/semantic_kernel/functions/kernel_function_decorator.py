# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import logging
import sys
from functools import wraps
from inspect import isasyncgenfunction, isclass, isgeneratorfunction, signature
from typing import Any, Callable, ForwardRef

if sys.version_info < (3, 10):
    from get_annotations import get_annotations
    from typing_extensions import Annotated
else:
    from inspect import get_annotations
    from typing import Annotated

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
        func_sig = signature(func)
        annotations = {name: None for name, _ in func_sig.parameters.items() if name != "self"}
        try:
            annotations.update(get_annotations(func, eval_str=True))
        except Exception as ex:
            logger.error(f"Failed to get annotations for function {func.__name__}: {ex}")
        logger.debug(f"{annotations=}")
        func.__kernel_function_parameters__ = [
            _parse_parameter(name, param) for name, param in annotations.items() if name != "return"
        ]
        defaults = getattr(func, "__defaults__", None)
        logger.debug(f"{defaults=}")
        if defaults:
            for index, default in enumerate(defaults):
                if default is None:
                    continue
                if func.__kernel_function_parameters__[index]:
                    func.__kernel_function_parameters__[index]["default_value"] = default
                    func.__kernel_function_parameters__[index]["is_required"] = False
        return_param_dict = {}
        if "return" in annotations:
            return_param_dict = _parse_parameter("return", annotations["return"])
        func.__kernel_function_return_type__ = return_param_dict.get("type_", "None")
        func.__kernel_function_return_description__ = return_param_dict.get("description", "")
        func.__kernel_function_return_required__ = return_param_dict.get("is_required", False)
        return func

    if func:
        return decorator(func)
    return decorator


def _parse_parameter(name: str, param: str | Annotated) -> dict[str, Any]:
    logger.debug(f"Parsing param: {name}")
    logger.debug(f"Parsing annotation: {param}")
    ret: dict[str, Any] = {"name": name}
    if not param:
        ret["type_"] = "Any"
        ret["is_required"] = True
        return ret
    if not isinstance(param, str):
        if hasattr(param, "default"):
            ret["default_value"] = param.default
            ret["is_required"] = False
        else:
            ret["is_required"] = True
        if hasattr(param, "__metadata__"):
            ret["description"] = param.__metadata__[0]
        if hasattr(param, "__origin__"):
            ret.update(_parse_parameter(name, param.__origin__))
        if hasattr(param, "__args__"):
            args = []
            for arg in param.__args__:
                if arg == NoneType:
                    ret["is_required"] = False
                    ret["default_value"] = None
                    continue
                if isinstance(arg, ForwardRef):
                    arg = arg.__forward_arg__
                args.append(_parse_parameter(name, arg))
            if ret.get("type_") in ["list", "dict"]:
                ret["type_"] = f"{ret['type_']}[{', '.join([arg['type_'] for arg in args])}]"
            elif len(args) > 1:
                ret["type_"] = ", ".join([arg["type_"] for arg in args])
            else:
                ret["type_"] = args[0]["type_"]
                ret["type_object"] = args[0].get("type_object", None)
                if def_value := args[0].get("default_value", None):
                    ret["default_value"] = def_value
        elif isclass(param):
            ret["type_"] = param.__name__
            ret["type_object"] = param
        else:
            ret["type_"] = str(param).replace(" |", ",")
    else:
        if "|" in param:
            param = param.replace(" |", ",")
        ret["type_"] = param
        ret["is_required"] = True
    return ret
