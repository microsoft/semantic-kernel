# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import operator
import sys
from abc import abstractmethod
from ast import AST, Lambda, NodeVisitor, expr, parse
from collections.abc import AsyncIterable, Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from inspect import Parameter, _empty, getsource, signature
from types import MappingProxyType, NoneType
from typing import Annotated, Any, ClassVar, Final, Generic, Literal, Protocol, TypeVar, overload, runtime_checkable

from pydantic import BaseModel, Field, ValidationError, model_validator
from pydantic.dataclasses import dataclass as pyd_dataclass

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.data._shared import (
    DEFAULT_FUNCTION_NAME,
    DEFAULT_PARAMETER_METADATA,
    DEFAULT_RETURN_PARAMETER_METADATA,
    DynamicFilterFunction,
    KernelSearchResults,
    SearchOptions,
    create_options,
    default_dynamic_filter_function,
)
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorSearchOptionsException,
    VectorStoreModelDeserializationException,
    VectorStoreModelException,
    VectorStoreModelSerializationException,
    VectorStoreModelValidationError,
    VectorStoreOperationException,
    VectorStoreOperationNotSupportedException,
)
from semantic_kernel.exceptions.search_exceptions import TextSearchException
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.kernel_types import OneOrList, OneOrMany, OptionalOneOrList, OptionalOneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.list_handler import desync_list

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

logger = logging.getLogger(__name__)


TModel = TypeVar("TModel", bound=object)
TKey = TypeVar("TKey")
_T = TypeVar("_T", bound="VectorStoreRecordHandler")
TFilters = TypeVar("TFilters")

DEFAULT_DESCRIPTION: Final[str] = (
    "Perform a vector search for data in a vector store, using the provided search options."
)


# region: Fields and Collection Definitions


@release_candidate
class FieldTypes(str, Enum):
    """Enumeration for field types in vector store models."""

    KEY = "key"
    VECTOR = "vector"
    DATA = "data"

    def __str__(self) -> str:
        """Return the string representation of the enum."""
        return self.value


@runtime_checkable
class SerializeMethodProtocol(Protocol):
    """Data model serialization protocol.

    This can optionally be implemented to allow single step serialization and deserialization
    for using your data model with a specific datastore.
    """

    def serialize(self, **kwargs: Any) -> Any:
        """Serialize the object to the format required by the data store."""
        ...  # pragma: no cover


@runtime_checkable
class ToDictFunctionProtocol(Protocol):
    """Protocol for to_dict function.

    Args:
        record: The record to be serialized.
        **kwargs: Additional keyword arguments.

    Returns:
        A list of dictionaries.
    """

    def __call__(self, record: Any, **kwargs: Any) -> Sequence[dict[str, Any]]: ...  # pragma: no cover


@runtime_checkable
class FromDictFunctionProtocol(Protocol):
    """Protocol for from_dict function.

    Args:
        records: A list of dictionaries.
        **kwargs: Additional keyword arguments.

    Returns:
        A record or list thereof.
    """

    def __call__(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Any: ...


@runtime_checkable
class SerializeFunctionProtocol(Protocol):
    """Protocol for serialize function.

    Args:
        record: The record to be serialized.
        **kwargs: Additional keyword arguments.

    Returns:
        The serialized record, ready to be consumed by the specific store.

    """

    def __call__(self, record: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class DeserializeFunctionProtocol(Protocol):
    """Protocol for deserialize function.

    Args:
        records: The serialized record directly from the store.
        **kwargs: Additional keyword arguments.

    Returns:
        The deserialized record in the format expected by the application.

    """

    def __call__(self, records: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class ToDictMethodProtocol(Protocol):
    """Class used internally to check if a model has a to_dict method."""

    def to_dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Serialize the object to the format required by the data store."""
        ...  # pragma: no cover


class IndexKind(str, Enum):
    """Index kinds for similarity search.

    HNSW
        Hierarchical Navigable Small World which performs an approximate nearest neighbor (ANN) search.
        Lower accuracy than exhaustive k nearest neighbor, but faster and more efficient.

    Flat
        Does a brute force search to find the nearest neighbors.
        Calculates the distances between all pairs of data points, so has a linear time complexity,
        that grows directly proportional to the number of points.
        Also referred to as exhaustive k nearest neighbor in some databases.
        High recall accuracy, but slower and more expensive than HNSW.
        Better with smaller datasets.

    IVF Flat
        Inverted File with Flat Compression.
        Designed to enhance search efficiency by narrowing the search area
        through the use of neighbor partitions or clusters.
        Also referred to as approximate nearest neighbor (ANN) search.

    Disk ANN
        Disk-based Approximate Nearest Neighbor algorithm designed for efficiently searching
        for approximate nearest neighbors (ANN) in high-dimensional spaces.
        The primary focus of DiskANN is to handle large-scale datasets that cannot fit entirely
        into memory, leveraging disk storage to store the data while maintaining fast search times.

    Quantized Flat
        Index that compresses vectors using DiskANN-based quantization methods for better efficiency in the kNN search.

    Dynamic
        Dynamic index allows to automatically switch from FLAT to HNSW indexes.

    Default
        Default index type.
        Used when no index type is specified.
        Will differ per vector store.

    """

    HNSW = "hnsw"
    FLAT = "flat"
    IVF_FLAT = "ivf_flat"
    DISK_ANN = "disk_ann"
    QUANTIZED_FLAT = "quantized_flat"
    DYNAMIC = "dynamic"
    DEFAULT = "default"


class DistanceFunction(str, Enum):
    """Distance functions for similarity search.

    Cosine Similarity
        the cosine (angular) similarity between two vectors
        measures only the angle between the two vectors, without taking into account the length of the vectors
        Cosine Similarity = 1 - Cosine Distance
        -1 means vectors are opposite
        0 means vectors are orthogonal
        1 means vectors are identical
    Cosine Distance
        the cosine (angular) distance between two vectors
        measures only the angle between the two vectors, without taking into account the length of the vectors
        Cosine Distance = 1 - Cosine Similarity
        2 means vectors are opposite
        1 means vectors are orthogonal
        0 means vectors are identical
    Dot Product
        measures both the length and angle between two vectors
        same as cosine similarity if the vectors are the same length, but more performant
    Euclidean Distance
        measures the Euclidean distance between two vectors
        also known as l2-norm
    Euclidean Squared Distance
        measures the Euclidean squared distance between two vectors
        also known as l2-squared
    Manhattan
        measures the Manhattan distance between two vectors
    Hamming
        number of differences between vectors at each dimensions
    DEFAULT
        default distance function
        used when no distance function is specified
        will differ per vector store.
    """

    COSINE_SIMILARITY = "cosine_similarity"
    COSINE_DISTANCE = "cosine_distance"
    DOT_PROD = "dot_prod"
    EUCLIDEAN_DISTANCE = "euclidean_distance"
    EUCLIDEAN_SQUARED_DISTANCE = "euclidean_squared_distance"
    MANHATTAN = "manhattan"
    HAMMING = "hamming"
    DEFAULT = "DEFAULT"


DISTANCE_FUNCTION_DIRECTION_HELPER: Final[dict[DistanceFunction, Callable[[int | float, int | float], bool]]] = {
    DistanceFunction.COSINE_SIMILARITY: operator.gt,
    DistanceFunction.COSINE_DISTANCE: operator.le,
    DistanceFunction.DOT_PROD: operator.gt,
    DistanceFunction.EUCLIDEAN_DISTANCE: operator.le,
    DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE: operator.le,
    DistanceFunction.MANHATTAN: operator.le,
    DistanceFunction.HAMMING: operator.le,
}


@release_candidate
@dataclass
class VectorStoreField:
    """Vector store fields."""

    field_type: Literal[FieldTypes.DATA, FieldTypes.KEY, FieldTypes.VECTOR] = FieldTypes.DATA
    name: str = ""
    storage_name: str | None = None
    type_: str | None = None
    # data specific fields (all optional)
    is_indexed: bool | None = None
    is_full_text_indexed: bool | None = None
    # vector specific fields (dimensions is mandatory)
    dimensions: int | None = None
    embedding_generator: EmbeddingGeneratorBase | None = None
    # defaults for these fields are not set here, because they are not relevant for data and key types
    index_kind: IndexKind | None = None
    distance_function: DistanceFunction | None = None

    @overload
    def __init__(
        self,
        field_type: Literal[FieldTypes.KEY, "key"] = FieldTypes.KEY,  # type: ignore[assignment]
        *,
        name: str | None = None,
        type: str | None = None,
        storage_name: str | None = None,
    ):
        """Key field of the record.

        When the key will be auto-generated by the store, make sure it has a default, usually None.

        Args:
            field_type: always "key".
            name: The name of the field.
            storage_name: The name of the field in the store, uses the field name by default.
            type: The type of the field.
        """
        ...

    @overload
    def __init__(
        self,
        field_type: Literal[FieldTypes.DATA, "data"] = FieldTypes.DATA,  # type: ignore[assignment]
        *,
        name: str | None = None,
        type: str | None = None,
        storage_name: str | None = None,
        is_indexed: bool | None = None,
        is_full_text_indexed: bool | None = None,
    ):
        """Data field in the record.

        Args:
            field_type: always "data".
            name: The name of the field.
            storage_name: The name of the field in the store, uses the field name by default.
            type: The type of the field.
            is_indexed: Whether the field is indexed.
            is_full_text_indexed: Whether the field is full text indexed.
        """
        ...

    @overload
    def __init__(
        self,
        field_type: Literal[FieldTypes.VECTOR, "vector"] = FieldTypes.VECTOR,  # type: ignore[assignment]
        *,
        name: str | None = None,
        type: str | None = None,
        dimensions: Annotated[int, Field(gt=0)],
        storage_name: str | None = None,
        index_kind: IndexKind | None = None,
        distance_function: DistanceFunction | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
    ):
        """Vector field in the record.

        This field should contain the value you want to use for the vector.
        When passing in the embedding generator, the embedding will be
        generated locally before upserting.
        If this is not set, the store should support generating the embedding for you.
        If you want to retrieve the original content of the vector,
        make sure to set this field twice,
        once with the VectorStoreRecordDataField and once with the VectorStoreRecordVectorField.

        If you want to be able to get the vectors back, make sure the type allows this, especially for pydantic models.
        For instance, if the input is a string, then the type annotation should be `str | list[float] | None`.

        If you want to cast the vector that is returned, you need to set the deserialize_function,
        for instance: `deserialize_function=np.array`, (with `import numpy as np` at the top of your file).
        If you want to set it up with more specific options, use a lambda, a custom function or a partial.

        Args:
            field_type: always "vector".
            name: The name of the field.
            storage_name: The name of the field in the store, uses the field name by default.
            type: Property type.
                For vectors this should be the inner type of the vector.
                By default the vector will be a list of numbers.
                If you want to use a numpy array or some other optimized format,
                set the cast_function with a function
                that takes a list of floats and returns a numpy array.
            dimensions: The number of dimensions of the vector, mandatory.
            index_kind: The index kind to use, uses a default index kind when None.
            distance_function: The distance function to use, uses a default distance function when None.
            embedding_generator: The embedding generator to use.
                If this is set, the embedding will be generated locally before upserting.
        """
        ...

    def __init__(
        self,
        field_type=FieldTypes.DATA,
        *,
        name=None,
        type=None,
        storage_name=None,
        is_indexed=None,
        is_full_text_indexed=None,
        dimensions=None,
        index_kind=None,
        distance_function=None,
        embedding_generator=None,
    ):
        """Vector store field."""
        self.field_type = field_type if isinstance(field_type, FieldTypes) else FieldTypes(field_type)
        # when a field is created, the name can be empty,
        # when a field get's added to a definition, the name needs to be there.
        if name:
            self.name = name
        self.storage_name = storage_name
        self.type_ = type
        self.is_indexed = is_indexed
        self.is_full_text_indexed = is_full_text_indexed
        if field_type == FieldTypes.VECTOR:
            if dimensions is None:
                raise ValidationError("Vector fields must specify 'dimensions'")
            self.dimensions = dimensions
            self.index_kind = index_kind or IndexKind.DEFAULT
            self.distance_function = distance_function or DistanceFunction.DEFAULT
            self.embedding_generator = embedding_generator


@release_candidate
class VectorStoreCollectionDefinition(KernelBaseModel):
    """Collection definition for vector stores.

    Args:
        fields: The fields of the record.
        container_mode: Whether the record is in container mode.
        to_dict: The to_dict function, should take a record and return a list of dicts.
        from_dict: The from_dict function, should take a list of dicts and return a record.
        deserialize: The deserialize function, should take a type specific to a datastore and return a record.

    """

    fields: list[VectorStoreField]
    key_name: str = Field(default="", init=False)
    container_mode: bool = False
    collection_name: str | None = None
    to_dict: ToDictFunctionProtocol | None = None
    from_dict: FromDictFunctionProtocol | None = None
    serialize: SerializeFunctionProtocol | None = None
    deserialize: DeserializeFunctionProtocol | None = None

    @property
    def names(self) -> list[str]:
        """Get the names of the fields."""
        return [field.name for field in self.fields]

    @property
    def storage_names(self) -> list[str]:
        """Get the names of the fields for storage."""
        return [field.storage_name or field.name for field in self.fields]

    @property
    def key_field(self) -> VectorStoreField:
        """Get the key field."""
        return next((field for field in self.fields if field.name == self.key_name), None)  # type: ignore

    @property
    def key_field_storage_name(self) -> str:
        """Get the key field storage name."""
        return self.key_field.storage_name or self.key_field.name

    @property
    def vector_fields(self) -> list[VectorStoreField]:
        """Get the names of the vector fields."""
        return [field for field in self.fields if field.field_type == FieldTypes.VECTOR]

    @property
    def data_fields(self) -> list[VectorStoreField]:
        """Get the names of the data fields."""
        return [field for field in self.fields if field.field_type == FieldTypes.DATA]

    @property
    def vector_field_names(self) -> list[str]:
        """Get the names of the vector fields."""
        return [field.name for field in self.fields if field.field_type == FieldTypes.VECTOR]

    @property
    def data_field_names(self) -> list[str]:
        """Get the names of all the data fields."""
        return [field.name for field in self.fields if field.field_type == FieldTypes.DATA]

    def try_get_vector_field(self, field_name: str | None = None) -> VectorStoreField | None:
        """Try to get the vector field.

        If the field_name is None, then the first vector field is returned.
        If no vector fields are present None is returned.

        Args:
            field_name: The field name.

        Returns:
            VectorStoreRecordVectorField | None: The vector field or None.
        """
        if field_name is None:
            if len(self.vector_fields) == 0:
                return None
            return self.vector_fields[0]
        for field in self.fields:
            if field.name == field_name or field.storage_name == field_name:
                if field.field_type == FieldTypes.VECTOR:
                    return field
                raise VectorStoreModelException(
                    f"Field {field_name} is not a vector field, it is of type {type(field).__name__}."
                )
        raise VectorStoreModelException(f"Field {field_name} not found.")

    def get_storage_names(self, include_vector_fields: bool = True, include_key_field: bool = True) -> list[str]:
        """Get the names of the fields for the storage.

        Args:
            include_vector_fields: Whether to include vector fields.
            include_key_field: Whether to include the key field.

        Returns:
            list[str]: The names of the fields.
        """
        return [
            field.storage_name or field.name
            for field in self.fields
            if field.field_type == FieldTypes.DATA
            or (field.field_type == FieldTypes.VECTOR and include_vector_fields)
            or (field.field_type == FieldTypes.KEY and include_key_field)
        ]

    def get_names(self, include_vector_fields: bool = True, include_key_field: bool = True) -> list[str]:
        """Get the names of the fields.

        Args:
            include_vector_fields: Whether to include vector fields.
            include_key_field: Whether to include the key field.

        Returns:
            list[str]: The names of the fields.
        """
        return [
            field.name
            for field in self.fields
            if field.field_type == FieldTypes.DATA
            or (field.field_type == FieldTypes.VECTOR and include_vector_fields)
            or (field.field_type == FieldTypes.KEY and include_key_field)
        ]

    def model_post_init(self, _: Any):
        """Validate the fields.

        Raises:
            VectorStoreModelException: If there is a field with an embedding property name
                but no corresponding vector field.
            VectorStoreModelException: If there is no key field.
        """
        if len(self.fields) == 0:
            raise VectorStoreModelException(
                "There must be at least one field with a VectorStoreRecordField annotation."
            )
        for field in self.fields:
            if not field.name or field.name == "":
                raise VectorStoreModelException("Field names must not be empty.")
            if field.field_type == FieldTypes.KEY:
                if self.key_name != "":
                    raise VectorStoreModelException("Memory record definition must have exactly one key field.")
                self.key_name = field.name
        if not self.key_name:
            raise VectorStoreModelException("Memory record definition must have exactly one key field.")


# region: Decorator


def _parse_vector_store_record_field_instance(record_field: VectorStoreField, field: Parameter) -> VectorStoreField:
    if not record_field.name or record_field.name != field.name:
        record_field.name = field.name
    if not record_field.type_ and hasattr(field.annotation, "__origin__"):
        property_type = field.annotation.__origin__
        if record_field.field_type == FieldTypes.VECTOR:
            if args := getattr(property_type, "__args__", None):
                if NoneType in args and len(args) > 1:
                    for arg in args:
                        if arg is NoneType:
                            continue

                        if (
                            (inner_args := getattr(arg, "__args__", None))
                            and len(inner_args) == 1
                            and inner_args[0] is not NoneType
                        ):
                            property_type = inner_args[0]
                            break
                        property_type = arg
                        break
                else:
                    property_type = args[0]

        else:
            if (args := getattr(property_type, "__args__", None)) and NoneType in args and len(args) == 2:
                property_type = args[0]

        record_field.type_ = str(property_type) if hasattr(property_type, "__args__") else property_type.__name__

    return record_field


def _parse_parameter_to_field(field: Parameter) -> VectorStoreField | None:
    # first check if there are any annotations
    if field.annotation is not _empty and hasattr(field.annotation, "__metadata__"):
        for field_annotation in field.annotation.__metadata__:
            if isinstance(field_annotation, VectorStoreField):
                return _parse_vector_store_record_field_instance(field_annotation, field)
    # This means there are no annotations or that all annotations are of other types.
    # we will check if there is a default, otherwise this will cause a runtime error.
    # because it will not be stored, and retrieving this object will fail without a default for this field.
    if field.default is _empty:
        raise VectorStoreModelException(
            "Fields that do not have a VectorStoreField annotation must have a default value."
        )
    logger.debug(f'Field "{field.name}" does not have a VectorStoreField annotation, will not be part of the record.')
    return None


def _parse_signature_to_definition(
    parameters: MappingProxyType[str, Parameter], collection_name: str | None = None
) -> VectorStoreCollectionDefinition:
    if len(parameters) == 0:
        raise VectorStoreModelException(
            "There must be at least one field in the datamodel. If you are using this with a @dataclass, "
            "you might have inverted the order of the decorators, the vectorstoremodel decorator should be the top one."
        )
    fields = []
    for param in parameters.values():
        field = _parse_parameter_to_field(param)
        if field:
            fields.append(field)

    return VectorStoreCollectionDefinition(
        fields=fields,
        collection_name=collection_name,
    )


@release_candidate
def vectorstoremodel(
    cls: type[TModel] | None = None,
    collection_name: str | None = None,
) -> type[TModel]:
    """Returns the class as a vector store model.

    This decorator makes a class a vector store model.
    There are three things being checked:
    - The class must have at least one field with a annotation,
        of type VectorStoreField.
    - The class must have exactly one field with the field_type `key`.
    - When creating a Vector Field, either supply the property type directly,
    or make sure to set the property that you want the index to use first.


    Args:
        cls: The class to be decorated.
        collection_name: The name of the collection to be used.
            This is used to set the collection name in the VectorStoreCollectionDefinition.

    Raises:
        VectorStoreModelException: If there are no fields with a VectorStoreField annotation.
        VectorStoreModelException: If there are fields with no name.
        VectorStoreModelException: If there is no key field.
    """

    def wrap(cls: type[TModel]) -> type[TModel]:
        # get fields and annotations
        cls_sig = signature(cls)
        setattr(cls, "__kernel_vectorstoremodel__", True)
        setattr(
            cls,
            "__kernel_vectorstoremodel_definition__",
            _parse_signature_to_definition(cls_sig.parameters, collection_name),
        )

        return cls  # type: ignore

    # See if we're being called as @vectorstoremodel or @vectorstoremodel().
    if cls is None:
        # We're called with parens.
        return wrap  # type: ignore

    # We're called as @vectorstoremodel without parens.
    return wrap(cls)


# region: VectorSearch Helpers


def _get_collection_name_from_model(
    record_type: type[TModel],
    definition: VectorStoreCollectionDefinition | None = None,
) -> str | None:
    """Get the collection name from the data model type or definition."""
    if record_type and not definition:
        definition = getattr(record_type, "__kernel_vectorstoremodel_definition__", None)
    if definition and definition.collection_name:
        return definition.collection_name
    return None


@pyd_dataclass
class GetFilteredRecordOptions:
    """Options for filtering records.

    Args:
        top: The maximum number of records to return.
        skip: The number of records to skip.
        order_by: A dictionary with fields names and a bool, True means ascending, False means descending.
    """

    top: int = 10
    skip: int = 0
    order_by: Mapping[str, bool] | None = None


class LambdaVisitor(NodeVisitor, Generic[TFilters]):
    """Visitor class to visit the AST nodes."""

    def __init__(self, lambda_parser: Callable[[expr], TFilters], output_filters: list[TFilters] | None = None) -> None:
        """Initialize the visitor with a lambda parser and output filters."""
        self.lambda_parser = lambda_parser
        self.output_filters = output_filters if output_filters is not None else []

    def visit_Lambda(self, node: Lambda) -> None:
        """This method is called when a lambda expression is found."""
        self.output_filters.append(self.lambda_parser(node.body))


@release_candidate
class SearchType(str, Enum):
    """Enumeration for search types.

    Contains: vector and keyword_hybrid.
    """

    VECTOR = "vector"
    KEYWORD_HYBRID = "keyword_hybrid"


@release_candidate
class VectorSearchOptions(SearchOptions):
    """Options for vector search, builds on TextSearchOptions.

    When multiple filters are used, they are combined with an AND operator.
    """

    vector_property_name: str | None = None
    additional_property_name: str | None = None
    top: Annotated[int, Field(gt=0)] = 3
    include_vectors: bool = False


@release_candidate
class VectorSearchResult(KernelBaseModel, Generic[TModel]):
    """The result of a vector search."""

    record: TModel
    score: float | None = None


# region: VectorStoreRecordHandler


@release_candidate
class VectorStoreRecordHandler(KernelBaseModel, Generic[TKey, TModel]):
    """Vector Store Record Handler class.

    This class is used to serialize and deserialize records to and from a vector store.
    As well as validating the data model against the vector store.
    It is subclassed by VectorStoreRecordCollection and VectorSearchBase.
    """

    record_type: type[TModel]
    definition: VectorStoreCollectionDefinition
    supported_key_types: ClassVar[set[str] | None] = None
    supported_vector_types: ClassVar[set[str] | None] = None
    embedding_generator: EmbeddingGeneratorBase | None = None

    @property
    def _key_field_name(self) -> str:
        return self.definition.key_name

    @property
    def _key_field_storage_name(self) -> str:
        return self.definition.key_field.storage_name or self.definition.key_name

    @property
    def _container_mode(self) -> bool:
        return self.definition.container_mode

    @model_validator(mode="before")
    @classmethod
    def _ensure_definition(cls: type[_T], data: Any) -> dict[str, Any]:
        """Ensure there is a  data model definition, if it isn't passed, try to get it from the data model type."""
        if isinstance(data, dict) and not data.get("definition"):
            data["definition"] = getattr(data["record_type"], "__kernel_vectorstoremodel_definition__", None)
        return data

    def model_post_init(self, __context: object | None = None):
        """Post init function that sets the key field and container mode values, and validates the datamodel."""
        self._validate_data_model()

    def _validate_data_model(self):
        """Internal function that can be overloaded by child classes to validate datatypes, etc.

        This should take the VectorStoreRecordDefinition from the item_type and validate it against the store.

        Checks can include, allowed naming of parameters, allowed data types, allowed vector dimensions.

        Default checks are that the key field is in the allowed key types and the vector fields
        are in the allowed vector types.

        Raises:
            VectorStoreModelValidationError: If the key field is not in the allowed key types.
            VectorStoreModelValidationError: If the vector fields are not in the allowed vector types.

        """
        if (
            self.supported_key_types
            and self.definition.key_field.type_
            and self.definition.key_field.type_ not in self.supported_key_types
        ):
            raise VectorStoreModelValidationError(
                f"Key field must be one of {self.supported_key_types}, got {self.definition.key_field.type_}"
            )
        if not self.supported_vector_types:
            return
        for field in self.definition.vector_fields:
            if field.type_ and field.type_ not in self.supported_vector_types:
                raise VectorStoreModelValidationError(
                    f"Vector field {field.name} must be one of {self.supported_vector_types}, got {field.type_}"
                )

    @abstractmethod
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        """Serialize a list of dicts of the data to the store model.

        This method should be overridden by the child class to convert the dict to the store model.
        """
        ...  # pragma: no cover

    @abstractmethod
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        """Deserialize the store models to a list of dicts.

        This method should be overridden by the child class to convert the store model to a list of dicts.
        """
        ...  # pragma: no cover

    # region Serialization methods

    async def serialize(self, records: OneOrMany[TModel], **kwargs: Any) -> OneOrMany[Any]:
        """Serialize the data model to the store model.

        This method follows the following steps:
        1. Check if the data model has a serialize method.
            Use that method to serialize and return the result.
        2. Serialize the records into a dict, using the data model specific method.
        3. Convert the dict to the store model, using the store specific method.

        If overriding this method, make sure to first try to serialize the data model to the store model,
        before doing the store specific version,
        the user supplied version should have precedence.

        Raises:
            VectorStoreModelSerializationException: If an error occurs during serialization.

        """
        try:
            if serialized := self._serialize_data_model_to_store_model(records):
                return serialized
        except VectorStoreModelSerializationException:
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorStoreModelSerializationException(f"Error serializing records: {exc}") from exc

        try:
            dict_records: list[dict[str, Any]] = []
            if not isinstance(records, list):
                records = [records]  # type: ignore
            for rec in records:
                dict_rec = self._serialize_data_model_to_dict(rec)
                if isinstance(dict_rec, list):
                    dict_records.extend(dict_rec)
                else:
                    dict_records.append(dict_rec)
        except VectorStoreModelSerializationException:
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorStoreModelSerializationException(f"Error serializing records: {exc}") from exc

        # add vectors
        try:
            dict_records = await self._add_vectors_to_records(dict_records)  # type: ignore
        except (VectorStoreModelException, VectorStoreOperationException):
            raise
        except Exception as exc:
            raise VectorStoreOperationException(
                "Exception occurred while trying to add the vectors to the records."
            ) from exc

        try:
            return self._serialize_dicts_to_store_models(dict_records, **kwargs)  # type: ignore
        except VectorStoreModelSerializationException:
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorStoreModelSerializationException(f"Error serializing records: {exc}") from exc

    def _serialize_data_model_to_store_model(self, record: OneOrMany[TModel], **kwargs: Any) -> OneOrMany[Any] | None:
        """Serialize the data model to the store model.

        This works when the data model has supplied a serialize method, specific to a data source.
        This is a method called 'serialize()' on the data model or part of the vector store record definition.

        The developer is responsible for correctly serializing for the specific data source.
        """
        if isinstance(record, Sequence):
            result = [self._serialize_data_model_to_store_model(rec, **kwargs) for rec in record]
            if not all(result):
                return None
            return result
        if self.definition.serialize:
            return self.definition.serialize(record, **kwargs)
        if isinstance(record, SerializeMethodProtocol):
            return record.serialize(**kwargs)
        return None

    def _serialize_data_model_to_dict(self, record: TModel, **kwargs: Any) -> OneOrList[dict[str, Any]]:
        """This function is used if no serialize method is found on the data model.

        This will generally serialize the data model to a dict, should not be overridden by child classes.

        The output of this should be passed to the serialize_dict_to_store_model method.
        """
        if self.definition.to_dict:
            return self.definition.to_dict(record, **kwargs)  # type: ignore
        if isinstance(record, BaseModel):
            return record.model_dump()

        store_model = {}
        for field in self.definition.fields:
            store_model[field.storage_name or field.name] = (
                record.get(field.name, None) if isinstance(record, Mapping) else getattr(record, field.name)
            )
        return store_model

    # region Deserialization methods

    def deserialize(self, records: OneOrMany[Any | dict[str, Any]], **kwargs: Any) -> OneOrMany[TModel] | None:
        """Deserialize the store model to the data model.

        This method follows the following steps:
        1. Check if the data model has a deserialize method.
            Use that method to deserialize and return the result.
        2. Deserialize the store model to a dict, using the store specific method.
        3. Convert the dict to the data model, using the data model specific method.

        Raises:
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        try:
            if not records:
                return None
            if deserialized := self._deserialize_store_model_to_data_model(records, **kwargs):
                return deserialized

            if isinstance(records, Sequence):
                dict_records = self._deserialize_store_models_to_dicts(records, **kwargs)
                return (
                    self._deserialize_dict_to_data_model(dict_records, **kwargs)
                    if self._container_mode
                    else [self._deserialize_dict_to_data_model(rec, **kwargs) for rec in dict_records]
                )

            dict_record = self._deserialize_store_models_to_dicts([records], **kwargs)[0]
            # regardless of mode, only 1 object is returned.
            return self._deserialize_dict_to_data_model(dict_record, **kwargs)
        except VectorStoreModelDeserializationException:
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorStoreModelDeserializationException(f"Error deserializing records: {exc}") from exc

    def _deserialize_store_model_to_data_model(self, record: OneOrMany[Any], **kwargs: Any) -> OneOrMany[TModel] | None:
        """Deserialize the store model to the data model.

        This works when the data model has supplied a deserialize method, specific to a data source.
        This uses a method called 'deserialize()' on the data model or part of the vector store record definition.

        The developer is responsible for correctly deserializing for the specific data source.
        """
        if self.definition.deserialize:
            if isinstance(record, Sequence):
                return self.definition.deserialize(record, **kwargs)
            return self.definition.deserialize([record], **kwargs)
        if func := getattr(self.record_type, "deserialize", None):
            if isinstance(record, Sequence):
                return [func(rec, **kwargs) for rec in record]
            return func(record, **kwargs)
        return None

    def _deserialize_dict_to_data_model(self, record: OneOrMany[dict[str, Any]], **kwargs: Any) -> TModel:
        """This function is used if no deserialize method is found on the data model.

        This method is the second step and will deserialize a dict to the data model,
        should not be overridden by child classes.

        The input of this should come from the _deserialized_store_model_to_dict function.
        """
        if self.definition.from_dict:
            if isinstance(record, Sequence):
                return self.definition.from_dict(record, **kwargs)
            ret = self.definition.from_dict([record], **kwargs)
            return ret if self._container_mode else ret[0]
        if isinstance(record, Sequence):
            if len(record) > 1:
                raise VectorStoreModelDeserializationException(
                    "Cannot deserialize multiple records to a single record unless you are using a container."
                )
            record = record[0]
        if func := getattr(self.record_type, "from_dict", None):
            return func(record)
        if issubclass(self.record_type, BaseModel):
            for field in self.definition.fields:
                if field.storage_name and field.storage_name in record:
                    record[field.name] = record.pop(field.storage_name)
            return self.record_type.model_validate(record)  # type: ignore
        data_model_dict: dict[str, Any] = {}
        for field in self.definition.fields:
            value = record.get(field.storage_name or field.name, None)
            if field.field_type == FieldTypes.VECTOR and not kwargs.get("include_vectors"):
                continue
            data_model_dict[field.name] = value
        if self.record_type is dict:
            return data_model_dict  # type: ignore
        return self.record_type(**data_model_dict)

    async def _add_vectors_to_records(
        self,
        records: OneOrMany[dict[str, Any]],
        **kwargs,
    ) -> OneOrMany[dict[str, Any]]:
        """Vectorize the vector record.

        This function can be passed to upsert or upsert batch of a VectorStoreRecordCollection.

        Loops through the fields of the data model definition,
        looks at data fields, if they have a vector field,
        looks up that vector field and checks if is a local embedding.

        If so adds that to a list of embeddings to make.

        Finally calls Kernel add_embedding_to_object with the list of embeddings to make.

        Optional arguments are passed onto the Kernel add_embedding_to_object call.
        """
        # dict of embedding_field.name and tuple of record, settings, field_name
        embeddings_to_make: list[tuple[str, int, EmbeddingGeneratorBase]] = []

        for field in self.definition.vector_fields:
            embedding_generator = field.embedding_generator or self.embedding_generator
            if not embedding_generator:
                continue
            if field.dimensions is None:
                raise VectorStoreModelException(
                    f"Field {field.name} has no dimensions, cannot create embedding for field."
                )
            embeddings_to_make.append((
                field.storage_name or field.name,
                field.dimensions,
                embedding_generator,
            ))

        for field_name, dimensions, embedder in embeddings_to_make:
            await self._add_embedding_to_object(
                inputs=records,
                field_name=field_name,
                dimensions=dimensions,
                embedding_generator=embedder,
                container_mode=self.definition.container_mode,
                **kwargs,
            )
        return records

    async def _add_embedding_to_object(
        self,
        inputs: OneOrMany[Any],
        field_name: str,
        dimensions: int,
        embedding_generator: EmbeddingGeneratorBase,
        container_mode: bool = False,
        **kwargs: Any,
    ):
        """Gather all fields to embed, batch the embedding generation and store."""
        contents: list[Any] = []
        dict_like = (getter := getattr(inputs, "get", False)) and callable(getter)
        list_of_dicts: bool = False
        if isinstance(inputs, list):
            list_of_dicts = (getter := getattr(inputs[0], "get", False)) and callable(getter)
            for record in inputs:
                if list_of_dicts:
                    contents.append(record.get(field_name))  # type: ignore
                else:
                    contents.append(getattr(record, field_name))
        else:
            if dict_like:
                contents.append(inputs.get(field_name))  # type: ignore
            else:
                contents.append(getattr(inputs, field_name))

        vectors = await embedding_generator.generate_raw_embeddings(
            texts=contents, settings=PromptExecutionSettings(dimensions=dimensions), **kwargs
        )  # type: ignore
        if vectors is None:
            raise VectorStoreOperationException("No vectors were generated.")
        if isinstance(inputs, list):
            for record, vector in zip(inputs, vectors):
                if list_of_dicts:
                    record[field_name] = vector  # type: ignore
                else:
                    setattr(record, field_name, vector)
            return
        if dict_like:
            inputs[field_name] = vectors[0]  # type: ignore
            return
        setattr(inputs, field_name, vectors[0])


# region: VectorStoreRecordCollection


@release_candidate
class VectorStoreCollection(VectorStoreRecordHandler[TKey, TModel], Generic[TKey, TModel]):
    """Base class for a vector store record collection."""

    collection_name: str = ""
    managed_client: bool = True

    @model_validator(mode="before")
    @classmethod
    def _ensure_collection_name(cls: type[_T], data: Any) -> dict[str, Any]:
        """Ensure there is a collection name, if it isn't passed, try to get it from the data model type."""
        if (
            isinstance(data, dict)
            and not data.get("collection_name")
            and (collection_name := _get_collection_name_from_model(data["record_type"], data.get("definition")))
        ):
            data["collection_name"] = collection_name
        return data

    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager.

        Should be overridden by subclasses, if necessary.

        If the client is passed in the constructor, it should not be closed,
        in that case the managed_client should be set to False.

        If the store supplied the managed client, it is responsible for closing it,
        and it should not be closed here and so managed_client should be False.

        Some services use two clients, one for the store and one for the collection,
        in that case, the collection client should be closed here,
        but the store client should only be closed when it is created in the collection.
        A additional flag might be needed for that.
        """
        pass

    @abstractmethod
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        """Upsert the records, this should be overridden by the child class.

        Args:
            records: The records, the format is specific to the store.
            **kwargs (Any): Additional arguments, to be passed to the store.

        Returns:
            The keys of the upserted records.

        Raises:
            Exception: If an error occurs during the upsert.
                There is no need to catch and parse exceptions in the inner functions,
                they are handled by the public methods.
                The only exception is raises exceptions yourself, such as a ValueError.
                This is then caught and turned into the relevant exception by the public method.
                This setup promotes a limited depth of the stack trace.

        """
        ...  # pragma: no cover

    @abstractmethod
    async def _inner_get(
        self,
        keys: Sequence[TKey] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs: Any,
    ) -> OneOrMany[Any] | None:
        """Get the records, this should be overridden by the child class.

        Args:
            keys: The keys to get.
            options: the options to use for the get.
            **kwargs: Additional arguments.

        Returns:
            The records from the store, not deserialized.

        Raises:
            Exception: If an error occurs during the upsert.
                There is no need to catch and parse exceptions in the inner functions,
                they are handled by the public methods.
                The only exception is raises exceptions yourself, such as a ValueError.
                This is then caught and turned into the relevant exception by the public method.
                This setup promotes a limited depth of the stack trace.
        """
        ...  # pragma: no cover

    @abstractmethod
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete the records, this should be overridden by the child class.

        Args:
            keys: The keys.
            **kwargs: Additional arguments.

        Raises:
            Exception: If an error occurs during the upsert.
                There is no need to catch and parse exceptions in the inner functions,
                they are handled by the public methods.
                The only exception is raises exceptions yourself, such as a ValueError.
                This is then caught and turned into the relevant exception by the public method.
                This setup promotes a limited depth of the stack trace.
        """
        ...  # pragma: no cover

    async def delete_create_collection(self, **kwargs: Any) -> None:
        """Create the collection in the service, after first trying to delete it.

        First uses does_collection_exist to check if it exists, if it does deletes it.
        Then, creates the collection.

        """
        if await self.does_collection_exist(**kwargs):
            await self.ensure_collection_deleted(**kwargs)
        await self.create_collection(**kwargs)

    async def ensure_collection_exists(self, **kwargs: Any) -> bool:
        """Create the collection in the service if it does not exists.

        First uses does_collection_exist to check if it exists, if it does returns False.
        Otherwise, creates the collection and returns True.

        Returns:
            bool: True if the collection was created, False if it already exists.

        """
        if await self.does_collection_exist(**kwargs):
            return False
        await self.create_collection(**kwargs)
        return True

    @abstractmethod
    async def create_collection(self, **kwargs: Any) -> None:
        """Create the collection in the service.

        This should be overridden by the child class.

        Raises:
            Make sure the implementation of this function raises relevant exceptions with good descriptions.
            This is different then the `_inner_x` methods, as this is a public method.

        """
        ...  # pragma: no cover

    @abstractmethod
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        """Check if the collection exists.

        This should be overridden by the child class.

        Raises:
            Make sure the implementation of this function raises relevant exceptions with good descriptions.
            This is different then the `_inner_x` methods, as this is a public method.
        """
        ...  # pragma: no cover

    @abstractmethod
    async def ensure_collection_deleted(self, **kwargs: Any) -> None:
        """Delete the collection.

        This should be overridden by the child class.

        Raises:
            Make sure the implementation of this function raises relevant exceptions with good descriptions.
            This is different then the `_inner_x` methods, as this is a public method.
        """
        ...  # pragma: no cover

    async def upsert(
        self,
        records: OneOrMany[TModel],
        **kwargs,
    ) -> OneOrMany[TKey]:
        """Upsert one or more records.

        If the key of the record already exists, the existing record will be updated.
        If the key does not exist, a new record will be created.

        Args:
            records: The records to upsert, can be a single record, a list of records, or a single container.
                If a single record is passed, a single key is returned, instead of a list of keys.
            **kwargs: Additional arguments.

        Returns:
            OneOrMany[TKey]: The keys of the upserted records.

        Raises:
            VectorStoreModelSerializationException: If an error occurs during serialization.
            VectorStoreOperationException: If an error occurs during upserting.
        """
        batch = True
        if not isinstance(records, list) and not self._container_mode:
            batch = False
        if records is None:
            raise VectorStoreOperationException("Either record or records must be provided.")

        try:
            data = await self.serialize(records)
        # the serialize method will parse any exception into a VectorStoreModelSerializationException
        except VectorStoreModelSerializationException:
            raise

        try:
            results = await self._inner_upsert(data if isinstance(data, list) else [data], **kwargs)  # type: ignore
        except Exception as exc:
            raise VectorStoreOperationException(f"Error upserting record(s): {exc}") from exc
        if batch or self._container_mode:
            return results
        return results[0]

    @overload
    async def get(
        self,
        top: int = ...,
        skip: int = ...,
        order_by: OneOrMany[str] | dict[str, bool] | None = None,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> Sequence[TModel] | None:
        """Get records based on the ordering and selection criteria.

        Args:
            include_vectors: Include the vectors in the response. Default is True.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            top: The number of records to return.
                Only used if keys are not provided.
            skip: The number of records to skip.
                Only used if keys are not provided.
            order_by: The order by clause,
                this can be a string, a list of strings or a dict,
                when passing strings, they are assumed to be ascending.
                Otherwise, use the value in the dict to set ascending (True) or descending (False).
                example: {"field_name": True} or ["field_name", {"field_name2": False}].
            **kwargs: Additional arguments.

        Returns:
            The records, either a list of TModel or the container type.

        Raises:
            VectorStoreOperationException: If an error occurs during the get.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        ...

    @overload
    async def get(
        self,
        key: TKey = ...,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> TModel | None:
        """Get a record if it exists.

        Args:
            key: The key to get.
            include_vectors: Include the vectors in the response. Default is True.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            **kwargs: Additional arguments.

        Returns:
            The records, either a list of TModel or the container type.

        Raises:
            VectorStoreOperationException: If an error occurs during the get.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        ...

    @overload
    async def get(
        self,
        keys: Sequence[TKey] = ...,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> OneOrMany[TModel] | None:
        """Get a batch of records whose keys exist in the collection, i.e. keys that do not exist are ignored.

        Args:
            keys: The keys to get, if keys are provided, key is ignored.
            include_vectors: Include the vectors in the response. Default is True.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            **kwargs: Additional arguments.

        Returns:
            The records, either a list of TModel or the container type.

        Raises:
            VectorStoreOperationException: If an error occurs during the get.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        ...

    async def get(
        self,
        key=None,
        keys=None,
        include_vectors=False,
        **kwargs,
    ):
        """Get a batch of records whose keys exist in the collection, i.e. keys that do not exist are ignored.

        Args:
            key: The key to get.
            keys: The keys to get, if keys are provided, key is ignored.
            include_vectors: Include the vectors in the response. Default is True.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            top: The number of records to return.
                Only used if keys are not provided.
            skip: The number of records to skip.
                Only used if keys are not provided.
            order_by: The order by clause, this is a list of dicts with the field name and ascending flag,
                (default is True, which means ascending).
                Only used if keys are not provided.
            **kwargs: Additional arguments.

        Returns:
            The records, either a list of TModel or the container type.

        Raises:
            VectorStoreOperationException: If an error occurs during the get.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        batch = True
        options = None
        if not keys and key:
            if not isinstance(key, list):
                keys = [key]
                batch = False
            else:
                keys = key
        if not keys:
            if kwargs:
                get_args = {}
                kw_order_by: OneOrList[str] | dict[str, bool] | None = kwargs.pop("order_by", None)  # type: ignore
                if "top" in kwargs:
                    get_args["top"] = kwargs.pop("top", None)
                if "skip" in kwargs:
                    get_args["skip"] = kwargs.pop("skip", None)
                order_by: dict[str, bool] | None = None
                if kw_order_by is not None:
                    order_by = {}
                    if isinstance(kw_order_by, str):
                        order_by[kw_order_by] = True
                    elif isinstance(kw_order_by, dict):
                        order_by = kw_order_by
                    elif isinstance(kw_order_by, list):
                        for item in kw_order_by:
                            if isinstance(item, str):
                                order_by[item] = True
                            else:
                                order_by.update(item)
                    else:
                        raise VectorStoreOperationException(
                            f"Invalid order_by type: {type(order_by)}, expected str, dict or list."
                        )
                    get_args["order_by"] = order_by
                try:
                    options = GetFilteredRecordOptions(**get_args)
                except Exception as exc:
                    raise VectorStoreOperationException(f"Error creating options: {exc}") from exc
            else:
                raise VectorStoreOperationException("Either key, keys or options must be provided.")
        try:
            records = await self._inner_get(keys, include_vectors=include_vectors, options=options, **kwargs)
        except Exception as exc:
            raise VectorStoreOperationException(f"Error getting record(s): {exc}") from exc

        if not records:
            return None

        try:
            model_records = self.deserialize(
                records if batch else records[0], include_vectors=include_vectors, **kwargs
            )
        # the deserialize method will parse any exception into a VectorStoreModelDeserializationException
        except VectorStoreModelDeserializationException:
            raise

        # there are many code paths within the deserialize method, some supplied by the developer,
        # and so depending on what is used,
        # it might return a sequence, so we just return the first element,
        # there should never be multiple elements (this is not a batch get),
        # hence a raise if there are.
        if batch:
            return model_records
        if not isinstance(model_records, Sequence):
            return model_records
        if len(model_records) == 1:
            return model_records[0]
        raise VectorStoreModelDeserializationException(
            f"Error deserializing record, multiple records returned: {model_records}"
        )

    async def delete(self, keys: OneOrMany[TKey], **kwargs):
        """Delete one or more records by key.

        An exception will be raised at the end if any record does not exist.

        Args:
            keys: The key or keys to be deleted.
            **kwargs: Additional arguments.
        Exceptions:
            VectorStoreOperationException: If an error occurs during deletion or a record does not exist.
        """
        if not isinstance(keys, list):
            keys = [keys]  # type: ignore
        try:
            await self._inner_delete(keys, **kwargs)  # type: ignore
        except Exception as exc:
            raise VectorStoreOperationException(f"Error deleting record(s): {exc}") from exc


# region: VectorStore


@release_candidate
class VectorStore(KernelBaseModel):
    """Base class for vector stores."""

    managed_client: bool = True
    embedding_generator: EmbeddingGeneratorBase | None = None

    @abstractmethod
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> "VectorStoreCollection":
        """Get a vector store record collection instance tied to this store.

        Args:
            record_type: The type of the records that will be used.
            definition: The data model definition.
            collection_name: The name of the collection.
            embedding_generator: The embedding generator to use.
            **kwargs: Additional arguments.

        Returns:
            A vector store record collection instance tied to this store.

        """
        ...  # pragma: no cover

    @abstractmethod
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        """Get the names of all collections."""
        ...  # pragma: no cover

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Check if a collection exists.

        This is a wrapper around the get_collection method of a collection,
        to check if the collection exists.
        """
        try:
            data_model = VectorStoreCollectionDefinition(fields=[VectorStoreField("key", name="id")])
            collection = self.get_collection(record_type=dict, definition=data_model, collection_name=collection_name)
            return await collection.does_collection_exist()
        except VectorStoreOperationException:
            return False

    async def ensure_collection_deleted(self, collection_name: str) -> None:
        """Delete a collection.

        This is a wrapper around the get_collection method of a collection,
        to delete the collection.
        """
        try:
            data_model = VectorStoreCollectionDefinition(fields=[VectorStoreField("key", name="id")])
            collection = self.get_collection(record_type=dict, definition=data_model, collection_name=collection_name)
            await collection.ensure_collection_deleted()
        except VectorStoreOperationException:
            pass

    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager.

        Should be overridden by subclasses, if necessary.

        If the client is passed in the constructor, it should not be closed,
        in that case the managed_client should be set to False.
        """
        pass  # pragma: no cover


# region: Vector Search


@release_candidate
class VectorSearch(VectorStoreRecordHandler[TKey, TModel], Generic[TKey, TModel]):
    """Base class for searching vectors."""

    supported_search_types: ClassVar[set[SearchType]] = Field(default_factory=set)

    @property
    def options_class(self) -> type[SearchOptions]:
        """The options class for the search."""
        return VectorSearchOptions

    @abstractmethod
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Inner search method.

        This is the main search method that should be implemented, and will be called by the public search methods.
        Currently, at least one of the three search contents will be provided
        (through the public interface mixin functions), in the future, this may be expanded to allow multiple of them.

        This method should return a KernelSearchResults object with the results of the search.
        The inner "results" object of the KernelSearchResults should be a async iterator that yields the search results,
        this allows things like paging to be implemented.

        There is a default helper method "_get_vector_search_results_from_results" to convert
        the results to a async iterable VectorSearchResults, but this can be overridden if necessary.

        Options might be a object of type VectorSearchOptions, or a subclass of it.

        The implementation of this method must deal with the possibility that multiple search contents are provided,
        and should handle them in a way that makes sense for that particular store.

        The public methods will catch and reraise the three exceptions mentioned below, others are caught and turned
        into a VectorSearchExecutionException.

        Args:
            search_type: The type of search to perform.
            options: The search options, can be None.
            values: The values to search for, optional.
            vector: The vector to search for, optional.
            **kwargs: Additional arguments that might be needed.

        Returns:
            The search results, wrapped in a KernelSearchResults object.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.

        """
        ...

    @abstractmethod
    def _get_record_from_result(self, result: Any) -> Any:
        """Get the record from the returned search result.

        Does any unpacking or processing of the result to get just the record.

        If the underlying SDK of the store returns a particular type that might include something
        like a score or other metadata, this method should be overridden to extract just the record.

        Likely returns a dict, but in some cases could return the record in the form of a SDK specific object.

        This method is used as part of the _get_vector_search_results_from_results method,
        the output of it is passed to the deserializer.
        """
        ...

    @abstractmethod
    def _get_score_from_result(self, result: Any) -> float | None:
        """Get the score from the result.

        Does any unpacking or processing of the result to get just the score.

        If the underlying SDK of the store returns a particular type with a score or other metadata,
        this method extracts it.
        """
        ...

    async def _get_vector_search_results_from_results(
        self, results: AsyncIterable[Any] | Sequence[Any], options: VectorSearchOptions | None = None
    ) -> AsyncIterable[VectorSearchResult[TModel]]:
        if isinstance(results, Sequence):
            results = desync_list(results)
        async for result in results:
            if not result:
                continue
            try:
                record = self.deserialize(
                    self._get_record_from_result(result), include_vectors=options.include_vectors if options else True
                )
            except VectorStoreModelDeserializationException:
                raise
            except Exception as exc:
                raise VectorStoreModelDeserializationException(
                    f"An error occurred while deserializing the record: {exc}"
                ) from exc
            score = self._get_score_from_result(result)
            if record is not None:
                # single records are always returned as single records by the deserializer
                yield VectorSearchResult(record=record, score=score)  # type: ignore

    @overload
    async def search(
        self,
        values: Any,
        *,
        vector_field_name: str | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 3,
        skip: int = 0,
        include_total_count: bool = False,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store with Vector search for records that match the given value and filter.

        Args:
            values: The values to search for. These will be vectorized,
                either by the store or using the provided generator.
            vector_field_name: The name of the vector field to use for the search.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            include_vectors: Whether to include the vectors in the results.
            kwargs: If options are not set, this is used to create them.
                they are passed on to the inner search method.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.

        """
        ...

    @overload
    async def search(
        self,
        *,
        vector: Sequence[float | int],
        vector_field_name: str | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 3,
        skip: int = 0,
        include_total_count: bool = False,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store with Vector search for records that match the given vector and filter.

        Args:
            vector: The vector to search for
            vector_field_name: The name of the vector field to use for the search.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            include_vectors: Whether to include the vectors in the results.
            kwargs: If options are not set, this is used to create them.
                they are passed on to the inner search method.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.

        """
        ...

    async def search(
        self,
        values=None,
        *,
        vector=None,
        vector_property_name=None,
        filter=None,
        top=3,
        skip=0,
        include_total_count=False,
        include_vectors=False,
        **kwargs,
    ):
        """Search the vector store for records that match the given value and filter.

        Args:
            values: The values to search for.
            vector: The vector to search for, if not provided, the values will be used to generate a vector.
            vector_property_name: The name of the vector property to use for the search.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            include_vectors: Whether to include the vectors in the results.
            kwargs: If options are not set, this is used to create them.
                they are passed on to the inner search method.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.

        """
        if SearchType.VECTOR not in self.supported_search_types:
            raise VectorStoreOperationNotSupportedException(
                f"Vector search is not supported by this vector store: {self.__class__.__name__}"
            )
        options = VectorSearchOptions(
            filter=filter,
            vector_property_name=vector_property_name,
            top=top,
            skip=skip,
            include_total_count=include_total_count,
            include_vectors=include_vectors,
        )
        try:
            return await self._inner_search(
                search_type=SearchType.VECTOR,
                values=values,
                options=options,
                vector=vector,
                **kwargs,
            )
        except (
            VectorStoreModelDeserializationException,
            VectorSearchOptionsException,
            VectorSearchExecutionException,
            VectorStoreOperationNotSupportedException,
            VectorStoreOperationException,
        ):
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorSearchExecutionException(f"An error occurred during the search: {exc}") from exc

    async def hybrid_search(
        self,
        values: Any,
        *,
        vector: list[float | int] | None = None,
        vector_property_name: str | None = None,
        additional_property_name: str | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 3,
        skip: int = 0,
        include_total_count: bool = False,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the vector store for records that match the given values and filter.

        Args:
            values: The values to search for.
            vector: The vector to search for, if not provided, the values will be used to generate a vector.
            vector_property_name: The name of the vector field to use for the search.
            additional_property_name: The name of the additional property field to use for the search.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            include_vectors: Whether to include the vectors in the results.
            kwargs: If options are not set, this is used to create them.
                they are passed on to the inner search method.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.

        """
        if SearchType.KEYWORD_HYBRID not in self.supported_search_types:
            raise VectorStoreOperationNotSupportedException(
                f"Keyword hybrid search is not supported by this vector store: {self.__class__.__name__}"
            )
        options = VectorSearchOptions(
            filter=filter,
            vector_property_name=vector_property_name,
            additional_property_name=additional_property_name,
            top=top,
            skip=skip,
            include_total_count=include_total_count,
            include_vectors=include_vectors,
        )
        try:
            return await self._inner_search(
                search_type=SearchType.KEYWORD_HYBRID,
                values=values,
                vector=vector,
                options=options,
                **kwargs,
            )
        except (
            VectorStoreModelDeserializationException,
            VectorSearchOptionsException,
            VectorSearchExecutionException,
            VectorStoreOperationNotSupportedException,
            VectorStoreOperationException,
        ):
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorSearchExecutionException(f"An error occurred during the search: {exc}") from exc

    async def _generate_vector_from_values(
        self,
        values: Any | None,
        options: VectorSearchOptions,
    ) -> Sequence[float | int] | None:
        """Generate a vector from the given keywords."""
        if values is None:
            return None
        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorSearchOptionsException(
                f"Vector field '{options.vector_property_name}' not found in data model definition."
            )
        embedding_generator = (
            vector_field.embedding_generator if vector_field.embedding_generator else self.embedding_generator
        )
        if not embedding_generator:
            raise VectorSearchOptionsException(
                f"Embedding generator not found for vector field '{options.vector_property_name}'."
            )

        return (
            await embedding_generator.generate_embeddings(
                # TODO (eavanvalkenburg): this only deals with string values, should support other types as well
                # but that requires work on the embedding generators first.
                texts=[values if isinstance(values, str) else json.dumps(values)],
                settings=PromptExecutionSettings(dimensions=vector_field.dimensions),
            )
        )[0].tolist()

    def _build_filter(self, search_filter: OptionalOneOrMany[Callable | str] | None) -> OptionalOneOrMany[Any]:
        """Create the filter based on the filters.

        This function returns None, a single filter, or a list of filters.
        If a single filter is passed, a single filter is returned.

        It takes the filters, which can be a Callable (lambda) or a string, and parses them into a filter object,
        using the _lambda_parser method that is specific to each vector store.

        If a list of filters, is passed, the parsed filters are also returned as a list, so the caller needs to
        combine them in the appropriate way.

        Often called like this (when filters are strings):
        ```python
        if filter := self._build_filter(options.filter):
            search_args["filter"] = filter if isinstance(filter, str) else " and ".join(filter)
        ```
        """
        if not search_filter:
            return None

        filters = search_filter if isinstance(search_filter, list) else [search_filter]

        created_filters: list[Any] = []

        visitor = LambdaVisitor(self._lambda_parser)
        for filter_ in filters:
            # parse lambda expression with AST
            tree = parse(filter_ if isinstance(filter_, str) else getsource(filter_).strip())
            visitor.visit(tree)
        created_filters = visitor.output_filters
        if len(created_filters) == 0:
            raise VectorStoreOperationException("No filter strings found.")
        if len(created_filters) == 1:
            return created_filters[0]
        return created_filters

    @abstractmethod
    def _lambda_parser(self, node: AST) -> Any:
        """Parse the lambda expression and return the filter string.

        This follows from the ast specs: https://docs.python.org/3/library/ast.html
        """
        # This method should be implemented in the derived class
        # to parse the lambda expression and return the filter string.
        pass

    def create_search_function(
        self,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        *,
        search_type: Literal["vector", "keyword_hybrid"] = "vector",
        parameters: list[KernelParameterMetadata] | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 5,
        skip: int = 0,
        vector_property_name: str | None = None,
        additional_property_name: str | None = None,
        include_vectors: bool = False,
        include_total_count: bool = False,
        filter_update_function: DynamicFilterFunction | None = None,
        string_mapper: Callable[[VectorSearchResult[TModel]], str] | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a search function.

        Args:
            function_name: The name of the function, to be used in the kernel, default is "search".
            description: The description of the function, a default is provided.
            search_type: The type of search to perform, can be 'vector' or 'keyword_hybrid'.
            parameters: The parameters for the function,
                use an empty list for a function without parameters,
                use None for the default set, which is "query", "top", and "skip".
            return_parameter: The return parameter for the function.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            vector_property_name: The name of the vector property to use for the search.
            additional_property_name: The name of the additional property field to use for the search.
            include_vectors: Whether to include the vectors in the results.
            include_total_count: Whether to include the total count of results.
            filter_update_function: A function to update the filters.
                The function should return the updated filter.
                The default function uses the parameters and the kwargs to update the filters, it
                adds equal to filters to the options for all parameters that are not "query".
                As well as adding equal to filters for parameters that have a default value.
            string_mapper: The function to map the search results to strings.
        """
        search_types = SearchType(search_type)
        if search_types not in self.supported_search_types:
            raise VectorStoreOperationNotSupportedException(
                f"Search type '{search_types.value}' is not supported by this vector store: {self.__class__.__name__}"
            )
        options = VectorSearchOptions(
            filter=filter,
            skip=skip,
            top=top,
            include_total_count=include_total_count,
            include_vectors=include_vectors,
            vector_property_name=vector_property_name,
            additional_property_name=additional_property_name,
        )
        return self._create_kernel_function(
            search_type=search_types,
            options=options,
            parameters=parameters,
            filter_update_function=filter_update_function,
            return_parameter=return_parameter,
            function_name=function_name,
            description=description,
            string_mapper=string_mapper,
        )

    def _create_kernel_function(
        self,
        search_type: SearchType,
        options: SearchOptions | None = None,
        parameters: list[KernelParameterMetadata] | None = None,
        filter_update_function: DynamicFilterFunction | None = None,
        return_parameter: KernelParameterMetadata | None = None,
        function_name: str = DEFAULT_FUNCTION_NAME,
        description: str = DEFAULT_DESCRIPTION,
        string_mapper: Callable[[VectorSearchResult[TModel]], str] | None = None,
    ) -> KernelFunction:
        """Create a kernel function from a search function."""
        update_func = filter_update_function or default_dynamic_filter_function

        @kernel_function(name=function_name, description=description)
        async def search_wrapper(**kwargs: Any) -> Sequence[str]:
            query = kwargs.pop("query", "")
            try:
                inner_options = create_options(self.options_class, deepcopy(options), **kwargs)
            except ValidationError:
                # this usually only happens when the kwargs are invalid, so blank options in this case.
                inner_options = self.options_class()
            inner_options.filter = update_func(filter=inner_options.filter, parameters=parameters, **kwargs)
            match search_type:
                case SearchType.VECTOR:
                    try:
                        results = await self.search(
                            values=query,
                            **inner_options.model_dump(exclude_defaults=True, exclude_none=True),
                        )
                    except Exception as e:
                        msg = f"Exception in search function: {e}"
                        logger.error(msg)
                        raise TextSearchException(msg) from e
                case SearchType.KEYWORD_HYBRID:
                    try:
                        results = await self.hybrid_search(
                            values=query,
                            **inner_options.model_dump(exclude_defaults=True, exclude_none=True),
                        )
                    except Exception as e:
                        msg = f"Exception in hybrid search function: {e}"
                        logger.error(msg)
                        raise TextSearchException(msg) from e
                case _:
                    raise VectorStoreOperationNotSupportedException(
                        f"Search type '{search_type}' is not supported by this vector store: {self.__class__.__name__}"
                    )
            if string_mapper:
                return [string_mapper(result) async for result in results.results]
            return [result.model_dump_json(exclude_none=True) async for result in results.results]

        return KernelFunctionFromMethod(
            method=search_wrapper,
            parameters=DEFAULT_PARAMETER_METADATA if parameters is None else parameters,
            return_parameter=return_parameter or DEFAULT_RETURN_PARAMETER_METADATA,
        )


@runtime_checkable
class VectorStoreCollectionProtocol(Protocol):  # noqa: D101
    collection_name: str
    record_type: object
    definition: VectorStoreCollectionDefinition
    supported_key_types: ClassVar[set[str]]
    supported_vector_types: ClassVar[set[str]]
    embedding_generator: EmbeddingGeneratorBase | None = None

    async def ensure_collection_exists(self, **kwargs: Any) -> bool:
        """Create the collection in the service if it does not exists.

        First uses does_collection_exist to check if it exists, if it does returns False.
        Otherwise, creates the collection and returns True.

        Args:
            **kwargs: Additional arguments.

        Returns:
            bool: True if the collection was created, False if it already exists.
        """
        ...

    async def create_collection(self, **kwargs: Any) -> None:
        """Create the collection in the service.

        Args:
            **kwargs: Additional arguments.

        Raises:
            Make sure the implementation of this function raises relevant exceptions with good descriptions.
        """
        ...

    async def does_collection_exist(self, **kwargs: Any) -> bool:
        """Check if the collection exists.

        Args:
            **kwargs: Additional arguments.

        Returns:
            bool: True if the collection exists, False otherwise.

        Raises:
            Make sure the implementation of this function raises relevant exceptions with good descriptions.
        """
        ...

    async def ensure_collection_deleted(self, **kwargs: Any) -> None:
        """Delete the collection.

        Args:
            **kwargs: Additional arguments.
        """
        ...

    async def get(
        self,
        key: Any = None,
        keys: Sequence[Any] | None = None,
        include_vectors: bool = False,
        top: int | None = None,
        skip: int | None = None,
        order_by: OneOrMany[str] | dict[str, bool] | None = None,
        **kwargs: Any,
    ) -> OptionalOneOrList[Any]:
        """Get a batch of records whose keys exist in the collection, i.e. keys that do not exist are ignored.

        Args:
            key: The key to get.
            keys: The keys to get, if keys are provided, key is ignored.
            include_vectors: Include the vectors in the response. Default is False.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            top: The number of records to return.
                Only used if keys are not provided.
            skip: The number of records to skip.
                Only used if keys are not provided.
            order_by: The order by clause,
                this can be a string, a list of strings or a dict,
                when passing strings, they are assumed to be ascending.
                Otherwise, use the value in the dict to set ascending (True) or descending (False).
                example: {"field_name": True} or ["field_name", {"field_name2": False}].
            **kwargs: Additional arguments.

        Returns:
            The records, either a list of TModel or the container type.

        Raises:
            VectorStoreOperationException: If an error occurs during the get.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        ...

    async def upsert(
        self,
        records: OneOrMany[Any],
        **kwargs: Any,
    ) -> OneOrMany[Any]:
        """Upsert one or more records.

        If the key of the record already exists, the existing record will be updated.
        If the key does not exist, a new record will be created.

        Args:
            records: The records to upsert, can be a single record, a list of records, or a single container.
                If a single record is passed, a single key is returned, instead of a list of keys.
            **kwargs: Additional arguments.

        Returns:
            OneOrMany[Any]: The keys of the upserted records.

        Raises:
            VectorStoreModelSerializationException: If an error occurs during serialization.
            VectorStoreOperationException: If an error occurs during upserting.
        """
        ...

    async def delete(self, keys: OneOrMany[Any], **kwargs: Any) -> None:
        """Delete one or more records by key.

        An exception will be raised at the end if any record does not exist.

        Args:
            keys: The key or keys to be deleted.
            **kwargs: Additional arguments.

        Raises:
            VectorStoreOperationException: If an error occurs during deletion or a record does not exist.
        """
        ...


@runtime_checkable
class VectorSearchProtocol(VectorStoreCollectionProtocol, Protocol):
    """Protocol to check that a collection supports vector search."""

    supported_search_types: ClassVar[set[SearchType]]

    async def search(
        self,
        values: Any = None,
        *,
        vector: Sequence[float | int] | None = None,
        vector_property_name: str | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 3,
        skip: int = 0,
        include_total_count: bool = False,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult]:
        """Search the vector store for records that match the given value and filter.

        Args:
            values: The values to search for. These will be vectorized,
                either by the store or using the provided generator.
            vector: The vector to search for, if not provided, the values will be used to generate a vector.
            vector_property_name: The name of the vector property to use for the search.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            include_vectors: Whether to include the vectors in the results.
            kwargs: If options are not set, this is used to create them.
                they are passed on to the inner search method.

        Returns:
            The search results.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.
        """
        ...

    async def hybrid_search(
        self,
        values: Any,
        *,
        vector: list[float | int] | None = None,
        vector_property_name: str | None = None,
        additional_property_name: str | None = None,
        filter: OptionalOneOrList[Callable | str] = None,
        top: int = 3,
        skip: int = 0,
        include_total_count: bool = False,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult]:
        """Search the vector store for records that match the given values and filter using hybrid search.

        Args:
            values: The values to search for.
            vector: The vector to search for, if not provided, the values will be used to generate a vector.
            vector_property_name: The name of the vector field to use for the search.
            additional_property_name: The name of the additional property field to use for the search.
            filter: The filter to apply to the search.
            top: The number of results to return.
            skip: The number of results to skip.
            include_total_count: Whether to include the total count of results.
            include_vectors: Whether to include the vectors in the results.
            kwargs: If options are not set, this is used to create them.
                they are passed on to the inner search method.

        Returns:
            The search results.

        Raises:
            VectorSearchExecutionException: If an error occurs during the search.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
            VectorSearchOptionsException: If the search options are invalid.
            VectorStoreOperationNotSupportedException: If the search type is not supported.
        """
        ...


__all__ = [
    "DEFAULT_DESCRIPTION",
    "DEFAULT_FUNCTION_NAME",
    "DEFAULT_PARAMETER_METADATA",
    "DEFAULT_RETURN_PARAMETER_METADATA",
    "DISTANCE_FUNCTION_DIRECTION_HELPER",
    "DistanceFunction",
    "DynamicFilterFunction",
    "FieldTypes",
    "IndexKind",
    "KernelSearchResults",
    "SearchType",
    "VectorSearch",
    "VectorSearchProtocol",
    "VectorSearchResult",
    "VectorStore",
    "VectorStoreCollection",
    "VectorStoreCollectionDefinition",
    "VectorStoreCollectionProtocol",
    "VectorStoreField",
    "create_options",
    "default_dynamic_filter_function",
    "vectorstoremodel",
]
