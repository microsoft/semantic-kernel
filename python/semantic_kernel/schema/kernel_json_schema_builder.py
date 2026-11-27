# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
import types
from contextvars import ContextVar
from enum import Enum
from functools import reduce
from operator import or_
from typing import Annotated, Any, ClassVar, ForwardRef, Literal, Union, get_args, get_origin, get_type_hints

from semantic_kernel.const import PARSED_ANNOTATION_UNION_DELIMITER
from semantic_kernel.exceptions.function_exceptions import FunctionInvalidParameterConfiguration
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)

# The models whose schema is being built further up the call stack.
_models_in_progress: ContextVar[tuple[Any, ...]] = ContextVar("_models_in_progress", default=())

TYPE_MAPPING = {
    int: "integer",
    str: "string",
    bool: "boolean",
    float: "number",
    list: "array",
    dict: "object",
    set: "array",
    tuple: "array",
    "int": "integer",
    "str": "string",
    "bool": "boolean",
    "float": "number",
    "list": "array",
    "dict": "object",
    "set": "array",
    "tuple": "array",
    "object": "object",
    "array": "array",
}


class KernelJsonSchemaBuilder:
    """Kernel JSON schema builder."""

    @classmethod
    def build(
        cls, parameter_type: type | str | Any, description: str | None = None, structured_output: bool = False
    ) -> dict[str, Any]:
        """Builds the JSON schema for a given parameter type and description.

        Args:
            parameter_type: The parameter type.
            description: The description of the parameter. Defaults to None.
            structured_output: Whether the outputs are structured. Defaults to False.

        Returns:
            dict[str, Any]: The JSON schema for the parameter type.
        """
        if isinstance(parameter_type, str):
            return cls.build_from_type_name(parameter_type, description)
        if isinstance(parameter_type, KernelBaseModel):
            return cls.build_model_schema(parameter_type, description, structured_output)
        if isinstance(parameter_type, type) and issubclass(parameter_type, Enum):
            return cls.build_enum_schema(parameter_type, description)
        if hasattr(parameter_type, "__annotations__"):
            return cls.build_model_schema(parameter_type, description, structured_output)
        if hasattr(parameter_type, "__args__"):
            return cls.handle_complex_type(parameter_type, description, structured_output)
        schema = cls.get_json_schema(parameter_type)
        if description:
            schema["description"] = description
        return schema

    @classmethod
    def build_model_schema(
        cls, model: type | KernelBaseModel, description: str | None = None, structured_output: bool = False
    ) -> dict[str, Any]:
        """Builds the JSON schema for a given model and description.

        Args:
            model: The model type.
            description: The description of the model. Defaults to None.
            structured_output: Whether the outputs are structured. Defaults to False.

        Returns:
            dict[str, Any]: The JSON schema for the model.
        """
        # TODO (moonbox3): add support for handling forward references, which is not currently tested
        # https://github.com/microsoft/semantic-kernel/issues/6464
        in_progress = _models_in_progress.get()
        if any(model is seen for seen in in_progress):
            # A resolved reference back to a model being built has no finite inline schema; use the placeholder.
            return cls.build_from_type_name("object", description)

        properties = {}
        required = []

        if not isinstance(model, type):
            model = type(model)
        model_module_globals = vars(sys.modules[model.__module__])
        hints = get_type_hints(model, globalns=model_module_globals, localns={})

        for field_name, field_type in hints.items():
            if field_type is ClassVar or get_origin(field_type) is ClassVar:
                # ClassVar annotations are class-level constants: pydantic
                # excludes them from model fields and serialized instances,
                # so they must not become (required) schema properties.
                continue
            field_type = cls.resolve_forward_refs(field_type, model_module_globals)
            field_description = None
            if hasattr(model, "model_fields") and field_name in model.model_fields:
                field_info = model.model_fields[field_name]
                field_description = getattr(field_info, "description", None)
                if field_description is None:
                    metadata = getattr(field_info, "metadata", None)
                    if isinstance(metadata, dict):
                        field_description = metadata.get("description")
                    elif isinstance(metadata, (list, tuple)):
                        for item in metadata:
                            if isinstance(item, str):
                                field_description = item
                                break
                            if isinstance(item, dict) and isinstance(item.get("description"), str):
                                field_description = item["description"]
                                break
            if not cls._is_optional(field_type):
                required.append(field_name)
            token = _models_in_progress.set((*in_progress, model))
            try:
                properties[field_name] = cls.build(field_type, field_description, structured_output)
            finally:
                _models_in_progress.reset(token)

        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        if structured_output:
            schema["additionalProperties"] = False  # type: ignore
        if description:
            schema["description"] = description

        return schema

    @classmethod
    def resolve_forward_refs(cls, annotation: Any, globalns: dict[str, Any]) -> Any:
        """Resolves forward references that annotation evaluation leaves behind.

        Kernel function parameters come from ``signature(func, eval_str=True)``, which evaluates an
        annotation that *is* a string and nothing below it, on every Python version. ``list["Inner"]``
        keeps its string, and unwrapping ``Optional["Inner"]`` or ``Annotated["Inner", ...]`` leaves a bare
        ``ForwardRef``. Unresolved, these fall through to the ``{"type": "object"}`` placeholder.

        Model fields come from ``get_type_hints``. On Python 3.10 it evaluates ``ForwardRef`` objects but
        not a bare ``str`` in a PEP 585 alias's ``__args__``, because ``list.__class_getitem__`` stores
        ``"Inner"`` verbatim. Python 3.11 made it wrap those strings itself (gh-85542), so on 3.11+ model
        field hints arrive fully resolved and come back from here unchanged.

        Args:
            annotation: The annotation to resolve.
            globalns: The namespace of the module owning the annotation.

        Returns:
            Any: The annotation, rebuilt with resolvable references replaced by their types. An alias
                that cannot be rebuilt is returned unchanged and a warning is logged.
        """
        if isinstance(annotation, (str, ForwardRef)):
            return cls._resolve_forward_ref_arg(annotation, globalns)
        origin = get_origin(annotation)
        args = get_args(annotation)
        if origin is None or not args:
            return annotation
        if origin is Literal:
            # Literal members are values, not names; a Literal["Inner"] must stay a string.
            return annotation
        if origin is Annotated:
            # Only the annotated type is a type; the metadata that follows it is left alone.
            return Annotated[(cls._resolve_forward_ref_arg(args[0], globalns), *args[1:])]

        resolved_args = tuple(cls._resolve_forward_ref_arg(arg, globalns) for arg in args)
        if resolved_args == args:
            return annotation

        try:
            return cls._rebuild_alias(origin, resolved_args)
        except TypeError as ex:
            # A failure here must not stop a function from being decorated, so keep the original alias and its
            # placeholder schema, but say so: a reference that did resolve has just been thrown away.
            logger.warning(f"Could not rebuild {annotation!r} with its forward references resolved: {ex}")
            return annotation

    @staticmethod
    def _rebuild_alias(origin: Any, args: tuple[Any, ...]) -> Any:
        """Rebuilds a generic alias from its origin and resolved arguments.

        Args:
            origin: The origin of the alias, as returned by ``get_origin``.
            args: The resolved arguments of the alias.

        Returns:
            Any: The rebuilt alias.

        Raises:
            TypeError: If the origin cannot be parameterized with these arguments.
        """
        if origin is types.UnionType:
            # Before Python 3.14 this is the origin of PEP 604 unions only and it is not subscriptable. From 3.14
            # it is also typing.Union, and joining the arguments is still correct for both spellings.
            return reduce(or_, args)
        # Special forms such as ClassVar and Final accept a single type, not a one element tuple.
        return origin[args[0] if len(args) == 1 else args]

    @classmethod
    def _resolve_forward_ref_arg(cls, arg: Any, globalns: dict[str, Any]) -> Any:
        """Resolves a single generic argument, recursing into nested generic aliases.

        Args:
            arg: The generic argument to resolve.
            globalns: The namespace to resolve the reference against.

        Returns:
            Any: The resolved type, or the argument unchanged when it cannot be resolved.
        """
        if isinstance(arg, str):
            return cls._lookup_type(arg, globalns, default=arg)
        if isinstance(arg, ForwardRef):
            return cls._lookup_type(arg.__forward_arg__, globalns, default=arg)
        if isinstance(arg, list):
            # Callable keeps its parameter types in a nested list.
            return [cls._resolve_forward_ref_arg(item, globalns) for item in arg]
        return cls.resolve_forward_refs(arg, globalns)

    @staticmethod
    def _lookup_type(name: str, globalns: dict[str, Any], default: Any) -> Any:
        """Looks a name up in the namespace, substituting it only when it names a usable type.

        A forward reference that happens to share its name with a module, a function or a plain
        value must not be rebuilt around that object: a module reaches ``build_model_schema`` and
        fails on ``__module__``, and a function or value would produce a misleading schema. The same
        goes for a class whose own type hints do not evaluate, for example hints on names imported only
        under ``TYPE_CHECKING``: ``build_model_schema`` would raise at function registration. Keeping
        the original reference lets the existing placeholder fallback apply instead.

        Args:
            name: The referenced name.
            globalns: The namespace to look it up in.
            default: What to return when the name is missing or does not name a usable type.

        Returns:
            Any: The class or typing construct the name refers to, or ``default``.
        """
        value = globalns.get(name, default)
        if get_origin(value) is not None:
            return value
        if not isinstance(value, type):
            return default
        try:
            get_type_hints(value, globalns=vars(sys.modules[value.__module__]), localns={})
        except Exception as ex:
            # Evaluating annotation strings can raise anything.
            logger.warning(f"Keeping forward reference {name!r} unresolved, its type hints do not evaluate: {ex}")
            return default
        return value

    @classmethod
    def _is_optional(cls, field_type: Any) -> bool:
        return get_origin(field_type) in {types.UnionType, Union} and type(None) in get_args(field_type)

    @classmethod
    def build_from_type_name(cls, parameter_type: str, description: str | None = None) -> dict[str, Any]:
        """Builds the JSON schema for a given parameter type name and description.

        Args:
            parameter_type (str): The parameter type name.
            description (str, optional): The description of the parameter. Defaults to None.

        Returns:
            dict[str, Any]: The JSON schema for the parameter type.
        """
        schema: dict[str, Any] = {}
        if PARSED_ANNOTATION_UNION_DELIMITER in parameter_type:
            # this means it is a Union or | so need to build with "anyOf"
            types = parameter_type.split(PARSED_ANNOTATION_UNION_DELIMITER)
            schemas = [cls.build_from_type_name(t.strip(), description) for t in types]
            schema["anyOf"] = schemas
        else:
            type_name = TYPE_MAPPING.get(parameter_type, "object")
            schema["type"] = type_name
            if description:
                schema["description"] = description
        return schema

    @classmethod
    def get_json_schema(cls, parameter_type: type) -> dict[str, Any]:
        """Gets JSON schema for a given parameter type.

        Args:
            parameter_type (type): The parameter type.

        Returns:
            dict[str, Any]: The JSON schema for the parameter type.
        """
        type_name = TYPE_MAPPING.get(parameter_type, "object")
        return {"type": type_name}

    @classmethod
    def handle_complex_type(
        cls, parameter_type: type, description: str | None = None, structured_output: bool = False
    ) -> dict[str, Any]:
        """Handles building the JSON schema for complex types.

        Args:
            parameter_type: The parameter type.
            description: The description of the parameter. Defaults to None.
            structured_output: Whether the outputs are structured. Defaults to False.

        Returns:
            dict[str, Any]: The JSON schema for the parameter type.
        """
        origin = get_origin(parameter_type)
        args = get_args(parameter_type)

        schema: dict[str, Any] = {}
        if origin is list or origin is set:
            item_type = args[0]
            schema = {
                "type": "array",
                "items": cls.build(item_type, structured_output=structured_output),
            }
            if description:
                schema["description"] = description
            return schema
        if origin is dict:
            _, value_type = args
            additional_properties = cls.build(value_type, structured_output=structured_output)
            if additional_properties == {"type": "object"}:
                additional_properties["properties"] = {}
            schema = {"type": "object", "additionalProperties": additional_properties}
            if description:
                schema["description"] = description
            if structured_output:
                schema["additionalProperties"] = False
            return schema
        if origin is tuple:
            if len(args) == 2 and args[1] is Ellipsis:
                # tuple[X, ...] holds any number of X, like list[X]
                schema = {"type": "array", "items": cls.build(args[0], structured_output=structured_output)}
            else:
                items = [cls.build(arg, structured_output=structured_output) for arg in args]
                schema = {"type": "array", "items": items}
            if description:
                schema["description"] = description
            if structured_output:
                schema["additionalProperties"] = False
            return schema
        if origin is Literal:
            values = [arg.value if isinstance(arg, Enum) else arg for arg in args]
            value_types = {"null" if v is None else TYPE_MAPPING.get(type(v), "string") for v in values}
            ordered_types = sorted(value_types, key=lambda t: (t == "null", t))
            schema = {"type": ordered_types[0] if len(ordered_types) == 1 else ordered_types, "enum": values}
            if description:
                schema["description"] = description
            return schema
        if origin in {Union, types.UnionType}:
            # Handle Optional[T] (Union[T, None]) by making schema nullable
            if len(args) == 2 and type(None) in args:
                non_none_type = args[0] if args[1] is type(None) else args[1]
                schema = cls.build(non_none_type, structured_output=structured_output)
                schema_types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
                schema["type"] = schema_types if "null" in schema_types else [*schema_types, "null"]
                if "enum" in schema and None not in schema["enum"]:
                    schema["enum"] = [*schema["enum"], None]
                if description:
                    schema["description"] = description
                if structured_output:
                    schema["additionalProperties"] = False
                return schema
            schemas = [cls.build(arg, description, structured_output=structured_output) for arg in args]
            return {"anyOf": schemas}
        schema = cls.get_json_schema(parameter_type)
        if description:
            schema["description"] = description
        if structured_output:
            schema["additionalProperties"] = False
        return schema

    @classmethod
    def build_enum_schema(cls, enum_type: type, description: str | None = None) -> dict[str, Any]:
        """Builds the JSON schema for an enum type.

        Args:
            enum_type (type): The enum type.
            description (str, optional): The description of the enum. Defaults to None.

        Returns:
            dict[str, Any]: The JSON schema for the enum type.
        """
        if not issubclass(enum_type, Enum):
            raise FunctionInvalidParameterConfiguration(f"{enum_type} is not a valid Enum type")

        try:
            enum_values = [item.value for item in enum_type]
        except TypeError as ex:
            raise FunctionInvalidParameterConfiguration(f"Failed to get enum values for {enum_type}") from ex
        schema = {"type": TYPE_MAPPING.get(type(enum_values[0]), "string"), "enum": enum_values}
        if description:
            schema["description"] = description
        return schema
