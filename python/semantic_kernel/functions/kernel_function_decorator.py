# Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
import logging
import types
from collections.abc import Callable
from inspect import (
    Parameter,
    Signature,
    isasyncgenfunction,
    isclass,
    isgeneratorfunction,
    signature,
)
from typing import Annotated, Any, ForwardRef, Union, get_args, get_origin

NoneType = type(None)
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======

import logging
from inspect import Parameter, Signature, isasyncgenfunction, isgeneratorfunction, signature
from typing import Callable, Optional, Tuple

>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
logger = logging.getLogger(__name__)


def kernel_function(
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    func: Callable[..., object] | None = None,
    name: str | None = None,
    description: str | None = None,
) -> Callable[..., Any]:
    """Decorator for kernel functions.

    Can be used directly as @kernel_function
    or with parameters @kernel_function(name='function', description='I am a function.').
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
):
    """
    Decorator for kernel functions.
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

    This decorator is used to mark a function as a kernel function. It also provides metadata for the function.
    The name and description can be left empty, and then the function name and docstring will be used.

    The parameters are parsed from the function signature, use typing.Annotated to provide a description for the
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    parameter.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    parameter.
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
    parameter.
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    parameter.
=======
    parameter, in python 3.8, use typing_extensions.Annotated.
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

    To parse the type, first it checks if the parameter is annotated, and get's the description from there.
    After that it checks recursively until it reaches the lowest level, and it combines
    the types into a single comma-separated string, a forwardRef is also supported.
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    All of this is are stored in __kernel_function_parameters__.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    All of this is are stored in __kernel_function_parameters__.
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
    All of this is are stored in __kernel_function_parameters__.
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    All of this is are stored in __kernel_function_parameters__.
=======
    All of this is are stored in __kernel_function_context_parameters__.
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

    The return type and description are parsed from the function signature,
    and that is stored in __kernel_function_return_type__, __kernel_function_return_description__
    and __kernel_function_return_required__.

    It also checks if the function is a streaming type (generator or iterable, async or not),
    and that is stored as a bool in __kernel_function_streaming__.

    Args:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
        func (Callable[..., object] | None): The function to decorate, can be None (if used as @kernel_function
        name (str | None): The name of the function, if not supplied, the function name will be used.
        description (str | None): The description of the function,
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        func (Callable[..., object] | None): The function to decorate, can be None (if used as @kernel_function
        name (str | None): The name of the function, if not supplied, the function name will be used.
        description (str | None): The description of the function,
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        func (Callable[..., object] | None): The function to decorate, can be None (if used as @kernel_function
        name (str | None): The name of the function, if not supplied, the function name will be used.
        description (str | None): The description of the function,
=======
        name (Optional[str]) -- The name of the function, if not supplied, the function name will be used.
        description (Optional[str]) -- The description of the function,
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
            if not supplied, the function docstring will be used, can be None.

    """

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        """The actual decorator function."""
        setattr(func, "__kernel_function__", True)
        setattr(func, "__kernel_function_description__", description or func.__doc__)
        setattr(
            func,
            "__kernel_function_name__",
            name or getattr(func, "__name__", "unknown"),
        )
        setattr(
            func,
            "__kernel_function_streaming__",
            isasyncgenfunction(func) or isgeneratorfunction(func),
        )
        logger.debug(
            f"Parsing decorator for function: {getattr(func, '__kernel_function_name__')}"
        )
        func_sig = signature(func, eval_str=True)

        annotations = _process_signature(func_sig)
        logger.debug(f"{annotations=}")

        setattr(func, "__kernel_function_parameters__", annotations)

        return_annotation = (
            _parse_parameter("return", func_sig.return_annotation, None)
            if func_sig.return_annotation
            else {}
        )
        setattr(
            func,
            "__kernel_function_return_type__",
            return_annotation.get("type_", "None"),
        )
        setattr(
            func,
            "__kernel_function_return_type_object__",
            return_annotation.get("type_object", None),
        )
        setattr(
            func,
            "__kernel_function_return_description__",
            return_annotation.get("description", ""),
        )
        setattr(
            func,
            "__kernel_function_return_required__",
            return_annotation.get("is_required", False),
        )
        return func

    if func:
        return decorator(func)
    return decorator


def _get_non_none_type(args: tuple) -> Any:
    """Return the first non-None type from args, or None if no such type exists or multiple non-None types are present."""  # noqa: E501
    non_none_types = [arg for arg in args if arg is not type(None)]
    # If we have more than one non-none type, we can't determine the single underlying type
    # so we rely on the type_ attribute, which means it's a Union and will be properly handled
    # later during schema generation
    if len(non_none_types) == 1:
        return non_none_types[0]
    return None


def _get_underlying_type(annotation: Any) -> Any:
    """Get the underlying type of the annotation."""
    if isinstance(annotation, types.UnionType):
        return _get_non_none_type(annotation.__args__)

    if hasattr(annotation, "__origin__"):
        if annotation.__origin__ is Union:
            return _get_non_none_type(get_args(annotation))

        if isinstance(annotation.__origin__, types.UnionType):
            return _get_non_none_type(annotation.__origin__.__args__)

        return annotation.__origin__

    return annotation


def _process_signature(func_sig: Signature) -> list[dict[str, Any]]:
    """Process the signature of the function."""
    annotations = []

    for arg in func_sig.parameters.values():
        if arg.name == "self":
            continue
        annotation = arg.annotation
        default = arg.default if arg.default != arg.empty else None
        parsed_annotation = _parse_parameter(arg.name, annotation, default)
        if get_origin(annotation) is Annotated or get_origin(annotation) in {
            Union,
            types.UnionType,
        }:
            underlying_type = _get_underlying_type(annotation)
        else:
            underlying_type = annotation
        parsed_annotation["type_object"] = underlying_type
        annotations.append(parsed_annotation)

    return annotations


def _parse_parameter(name: str, param: Any, default: Any) -> dict[str, Any]:
    """Parse the parameter annotation."""
    logger.debug(f"Parsing param: {name}")
    logger.debug(f"Parsing annotation: {param}")
    ret: dict[str, Any] = {"name": name}
    if default is not None:
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
                ret["type_"] = (
                    f"{ret['type_']}[{', '.join([arg['type_'] for arg in args])}]"
                )
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
