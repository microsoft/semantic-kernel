# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable
from inspect import Parameter, isasyncgenfunction, isclass, isgeneratorfunction, signature
from typing import Any, ForwardRef

NoneType = type(None)
logger = logging.getLogger(__name__)


def kernel_function(
    func: Callable[..., object] | None = None,
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

    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        setattr(func, "__kernel_function__", True)
        setattr(func, "__kernel_function_description__", description or func.__doc__)
        setattr(func, "__kernel_function_name__", name or getattr(func, "__name__", "unknown"))
        setattr(func, "__kernel_function_streaming__", isasyncgenfunction(func) or isgeneratorfunction(func))
        logger.debug(f"Parsing decorator for function: {getattr(func, '__kernel_function_name__')}")
        func_sig = signature(func, eval_str=True)
        annotations = []
        for arg in func_sig.parameters.values():
            if arg.name == "self":
                continue
            if arg.default == arg.empty:
                annotations.append(_parse_parameter(arg.name, arg.annotation, None))
            else:
                annotations.append(_parse_parameter(arg.name, arg.annotation, arg.default))
        logger.debug(f"{annotations=}")
        setattr(func, "__kernel_function_parameters__", annotations)

        return_annotation = (
            _parse_parameter("return", func_sig.return_annotation, None) if func_sig.return_annotation else {}
        )
        setattr(func, "__kernel_function_return_type__", return_annotation.get("type_", "None"))
        setattr(func, "__kernel_function_return_type_object__", return_annotation.get("type_object", None))
        setattr(func, "__kernel_function_return_description__", return_annotation.get("description", ""))
        setattr(func, "__kernel_function_return_required__", return_annotation.get("is_required", False))
        return func

    if func:
        return decorator(func)
    return decorator


def _parse_parameter(name: str, param: Any, default: Any) -> dict[str, Any]:
    logger.debug(f"Parsing param: {name}")
    logger.debug(f"Parsing annotation: {param}")
    ret: dict[str, Any] = {"name": name}
    if default:
        ret["default_value"] = default
        ret["is_required"] = False
    else:
        ret["is_required"] = True
    if not param or param == Parameter.empty:
        ret["type_"] = "Any"
        return ret
    if not isinstance(param, str):
        if hasattr(param, "__metadata__"):
            ret["description"] = param.__metadata__[0]
        if hasattr(param, "__origin__"):
            ret.update(_parse_parameter(name, param.__origin__, default))
        if hasattr(param, "__args__"):
            args = []
            for arg in param.__args__:
                if arg == NoneType:
                    ret["is_required"] = False
                    if "default_value" not in ret:
                        ret["default_value"] = None
                    continue
                if isinstance(arg, ForwardRef):
                    arg = arg.__forward_arg__
                args.append(_parse_parameter(name, arg, default))
            if ret.get("type_") in ["list", "dict"]:
                ret["type_"] = f"{ret['type_']}[{', '.join([arg['type_'] for arg in args])}]"
            elif len(args) > 1:
                ret["type_"] = ", ".join([arg["type_"] for arg in args])
            else:
                ret["type_"] = args[0]["type_"]
                ret["type_object"] = args[0].get("type_object", None)
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
