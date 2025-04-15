# Copyright (c) Microsoft. All rights reserved.

import logging
import types
from collections.abc import Callable
from inspect import Parameter, Signature, isasyncgenfunction, isclass, isgeneratorfunction, signature
from typing import Annotated, Any, ForwardRef, Union, get_args, get_origin

NoneType = type(None)
logger = logging.getLogger(__name__)


def kernel_function(
    func: Callable[..., object] | None = None,
    name: str | None = None,
    description: str | None = None,
) -> Callable[..., Any]:
    """Decorator for kernel functions.

    Can be used directly as @kernel_function
    or with parameters @kernel_function(name='function', description='I am a function.').

    This decorator is used to mark a function as a kernel function. It also provides metadata for the function.
    The name and description can be left empty, and then the function name and docstring will be used.

    The parameters are parsed from the function signature, use typing.Annotated to provide a description for the
    parameter.

    To parse the type, first it checks if the parameter is annotated.

    If there are annotations, the first annotation that is a string is used as the description.
    Any other annotations are checked if they are a dict, if so, they will be added to the parameter info.
    If the keys align with the KernelParameterMetadata, they will be added to the parameter info.
    This is useful for things like parameters like `kernel`, `service` and `arguments`, for instance
    if you set `{"include_in_function_choices": False}` in the annotation, that parameter will not be included in
    the representation of the function towards LLM's or MCP Servers. If you do set this and the parameter is required
    but you do not set it in a invoke level arguments, the function will raise an error.

    After the annotations, it checks recursively until it reaches the lowest level, and it combines
    the types into a single comma-separated string, a forwardRef is also supported.

    All of this is are stored in __kernel_function_parameters__.

    The return type and description are parsed from the function signature,
    and that is stored in __kernel_function_return_type__, __kernel_function_return_description__
    and __kernel_function_return_required__.

    It also checks if the function is a streaming type (generator or iterable, async or not),
    and that is stored as a bool in __kernel_function_streaming__.

    Args:
        func (Callable[..., object] | None): The function to decorate, can be None (if used as @kernel_function
        name (str | None): The name of the function, if not supplied, the function name will be used.
        description (str | None): The description of the function,
            if not supplied, the function docstring will be used, can be None.

    """

    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        """The actual decorator function."""
        setattr(func, "__kernel_function__", True)
        setattr(func, "__kernel_function_description__", description or func.__doc__)
        setattr(func, "__kernel_function_name__", name or getattr(func, "__name__", "unknown"))
        setattr(func, "__kernel_function_streaming__", isasyncgenfunction(func) or isgeneratorfunction(func))
        logger.debug(f"Parsing decorator for function: {getattr(func, '__kernel_function_name__')}")
        func_sig = signature(func, eval_str=True)

        annotations = _process_signature(func_sig)
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
        if get_origin(annotation) is Annotated or get_origin(annotation) in {Union, types.UnionType}:
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
            for meta in param.__metadata__:
                if isinstance(meta, str):
                    ret["description"] = meta
                elif isinstance(meta, dict):
                    # only override from the metadata if it is not already set
                    if "description" not in ret and (description := meta.pop("description", None)):
                        ret["description"] = description
                    ret.update(meta)
                else:
                    logger.debug(f"Unknown metadata type: {meta}")
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
    # if the include_in_function_choices is set to false, we set the is_required to false
    if not ret.get("include_in_function_choices", True):
        ret["is_required"] = False
    return ret
