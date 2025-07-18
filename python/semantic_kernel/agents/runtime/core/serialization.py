# Copyright (c) Microsoft. All rights reserved.

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields
from typing import Any, ClassVar, Protocol, TypeVar, cast, get_args, get_origin, runtime_checkable

from google.protobuf import any_pb2
from google.protobuf.message import Message
from pydantic import BaseModel

from semantic_kernel.agents.runtime.core.type_helpers import is_union
from semantic_kernel.utils.feature_stage_decorator import experimental

T = TypeVar("T")


@experimental
class MessageSerializer(Protocol[T]):
    """Serializer for messages."""

    @property
    def data_content_type(self) -> str:
        """Content type of the data being serialized."""
        ...

    @property
    def type_name(self) -> str:
        """Type name of the message being serialized."""
        ...

    def deserialize(self, payload: bytes) -> T:
        """Deserialize the payload into a message."""
        ...

    def serialize(self, message: T) -> bytes:
        """Serialize the message into a payload."""
        ...


@experimental
@runtime_checkable
class IsDataclass(Protocol):
    """Protocol to check if a class is a dataclass."""

    # as already noted in comments, checking for this attribute is currently
    # the most reliable way to ascertain that something is a dataclass
    __dataclass_fields__: ClassVar[dict[str, Any]]


@experimental
def is_dataclass(cls: type[Any]) -> bool:
    """Check if the class is a dataclass."""
    return hasattr(cls, "__dataclass_fields__")


@experimental
def has_nested_dataclass(cls: type[IsDataclass]) -> bool:
    """Check if the dataclass has nested dataclasses."""
    # iterate fields and check if any of them are dataclasses
    return any(is_dataclass(f.type) for f in cls.__dataclass_fields__.values())


@experimental
def contains_a_union(cls: type[IsDataclass]) -> bool:
    """Check if the dataclass contains a union type."""
    return any(is_union(f.type) for f in cls.__dataclass_fields__.values())


@experimental
def has_nested_base_model(cls: type[IsDataclass]) -> bool:
    """Check if the dataclass has nested Pydantic BaseModel."""
    for f in fields(cls):
        field_type = f.type
        # Resolve forward references and other annotations
        origin = get_origin(field_type)
        args = get_args(field_type)

        # If the field type is directly a subclass of BaseModel
        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            return True

        # If the field type is a generic type like List[BaseModel], Tuple[BaseModel, ...], etc.
        if origin is not None and args:
            for arg in args:
                # Recursively check the argument types
                if (isinstance(arg, type) and issubclass(arg, BaseModel)) or (
                    get_origin(arg) is not None and has_nested_base_model_in_type(arg)
                ):
                    return True
        # Handle Union types
        elif args:
            for arg in args:
                if (isinstance(arg, type) and issubclass(arg, BaseModel)) or (
                    get_origin(arg) is not None and has_nested_base_model_in_type(arg)
                ):
                    return True
    return False


@experimental
def has_nested_base_model_in_type(tp: Any) -> bool:
    """Helper function to check if a type or its arguments is a BaseModel subclass."""
    origin = get_origin(tp)
    args = get_args(tp)

    if isinstance(tp, type) and issubclass(tp, BaseModel):
        return True
    if origin is not None and args:
        for arg in args:
            if has_nested_base_model_in_type(arg):
                return True
    return False


DataclassT = TypeVar("DataclassT", bound=IsDataclass)

JSON_DATA_CONTENT_TYPE = "application/json"
"""JSON data content type"""

# TODO(evmattso): what's the correct content type? There seems to be some disagreement over what it should be
PROTOBUF_DATA_CONTENT_TYPE = "application/x-protobuf"
"""Protobuf data content type"""


@experimental
class DataclassJsonMessageSerializer(MessageSerializer[DataclassT]):
    """Serializer for dataclass messages."""

    def __init__(self, cls: type[DataclassT]) -> None:
        """Initialize the serializer with a dataclass type."""
        if contains_a_union(cls):
            raise ValueError("Dataclass has a union type, which is not supported. To use a union, use a Pydantic model")

        if has_nested_dataclass(cls) or has_nested_base_model(cls):
            raise ValueError(
                "Dataclass has nested dataclasses or base models, which are not supported. To use nested types, "
                "use a Pydantic model"
            )

        self.cls = cls

    @property
    def data_content_type(self) -> str:
        """Return the data content type."""
        return JSON_DATA_CONTENT_TYPE

    @property
    def type_name(self) -> str:
        """Return the type name."""
        return _type_name(self.cls)

    def deserialize(self, payload: bytes) -> DataclassT:
        """Deserialize the payload into a dataclass message."""
        message_str = payload.decode("utf-8")
        return self.cls(**json.loads(message_str))

    def serialize(self, message: DataclassT) -> bytes:
        """Serialize the dataclass message into a payload."""
        return json.dumps(asdict(message)).encode("utf-8")


PydanticT = TypeVar("PydanticT", bound=BaseModel)


@experimental
class PydanticJsonMessageSerializer(MessageSerializer[PydanticT]):
    """Serializer for Pydantic messages."""

    def __init__(self, cls: type[PydanticT]) -> None:
        """Initialize the serializer with a Pydantic model type."""
        self.cls = cls

    @property
    def data_content_type(self) -> str:
        """Return the data content type."""
        return JSON_DATA_CONTENT_TYPE

    @property
    def type_name(self) -> str:
        """Return the type name."""
        return _type_name(self.cls)

    def deserialize(self, payload: bytes) -> PydanticT:
        """Deserialize the payload into a Pydantic model message."""
        message_str = payload.decode("utf-8")
        return self.cls.model_validate_json(message_str)

    def serialize(self, message: PydanticT) -> bytes:
        """Serialize the Pydantic model message into a payload."""
        return message.model_dump_json().encode("utf-8")


ProtobufT = TypeVar("ProtobufT", bound=Message)


# This class serializes to and from a google.protobuf.Any message that has been serialized to a string
@experimental
class ProtobufMessageSerializer(MessageSerializer[ProtobufT]):
    """Serializer for Protobuf messages."""

    def __init__(self, cls: type[ProtobufT]) -> None:
        """Initialize the serializer with a Protobuf message type."""
        self.cls = cls

    @property
    def data_content_type(self) -> str:
        """Return the data content type."""
        return PROTOBUF_DATA_CONTENT_TYPE

    @property
    def type_name(self) -> str:
        """Return the type name."""
        return _type_name(self.cls)

    def deserialize(self, payload: bytes) -> ProtobufT:
        """Deserialize the payload into a Protobuf message."""
        # Parse payload into a proto any
        any_proto = any_pb2.Any()
        any_proto.ParseFromString(payload)

        destination_message = self.cls()

        if not any_proto.Unpack(destination_message):  # type: ignore
            raise ValueError(f"Failed to unpack payload into {self.cls}")

        return destination_message

    def serialize(self, message: ProtobufT) -> bytes:
        """Serialize the Protobuf message into a payload."""
        any_proto = any_pb2.Any()
        any_proto.Pack(message)  # type: ignore
        return any_proto.SerializeToString()


@experimental
@dataclass
class UnknownPayload:
    """Class to represent an unknown payload."""

    type_name: str
    data_content_type: str
    payload: bytes


def _type_name(cls: type[Any] | Any) -> str:
    # If cls is a protobuf, then we need to determine the descriptor
    if isinstance(cls, type):
        if issubclass(cls, Message):
            return cast(str, cls.DESCRIPTOR.full_name)  # type: ignore
    elif isinstance(cls, Message):
        return cast(str, cls.DESCRIPTOR.full_name)

    if isinstance(cls, type):
        return cls.__name__
    return cast(str, cls.__class__.__name__)


V = TypeVar("V")


@experimental
def try_get_known_serializers_for_type(cls: type[Any]) -> list[MessageSerializer[Any]]:
    """Try to get known serializers for a type."""
    serializers: list[MessageSerializer[Any]] = []
    if issubclass(cls, BaseModel):
        serializers.append(PydanticJsonMessageSerializer(cls))
    elif is_dataclass(cls):
        serializers.append(DataclassJsonMessageSerializer(cls))
    elif issubclass(cls, Message):
        serializers.append(ProtobufMessageSerializer(cls))

    return serializers


@experimental
class SerializationRegistry:
    """Serialization registry for messages."""

    def __init__(self) -> None:
        """Initialize the serialization registry."""
        # type_name, data_content_type -> serializer
        self._serializers: dict[tuple[str, str], MessageSerializer[Any]] = {}

    def add_serializer(self, serializer: MessageSerializer[Any] | Sequence[MessageSerializer[Any]]) -> None:
        """Add a new serializer to the registry."""
        if isinstance(serializer, Sequence):
            for c in serializer:
                self.add_serializer(c)
            return

        self._serializers[serializer.type_name, serializer.data_content_type] = serializer

    def deserialize(self, payload: bytes, *, type_name: str, data_content_type: str) -> Any:
        """Deserialize a payload into a message."""
        serializer = self._serializers.get((type_name, data_content_type))
        if serializer is None:
            return UnknownPayload(type_name, data_content_type, payload)

        return serializer.deserialize(payload)

    def serialize(self, message: Any, *, type_name: str, data_content_type: str) -> bytes:
        """Serialize a message into a payload."""
        serializer = self._serializers.get((type_name, data_content_type))
        if serializer is None:
            raise ValueError(f"Unknown type {type_name} with content type {data_content_type}")

        return serializer.serialize(message)

    def is_registered(self, type_name: str, data_content_type: str) -> bool:
        """Check if a type is registered in the registry."""
        return (type_name, data_content_type) in self._serializers

    def type_name(self, message: Any) -> str:
        """Get the type name of a message."""
        return _type_name(message)
