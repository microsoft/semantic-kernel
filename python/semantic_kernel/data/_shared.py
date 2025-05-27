# Copyright (c) Microsoft. All rights reserved.
# Classes in this file are shared between text search and vectors.
# They should not be imported directly, as they are also exposed in both modules.

from abc import ABC
from collections.abc import AsyncIterable, Callable, Mapping
from logging import Logger
from typing import Annotated, Any, Final, Generic, Protocol, TypeVar

from pydantic import ConfigDict, Field

from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.kernel_types import OptionalOneOrList
from semantic_kernel.utils.feature_stage_decorator import release_candidate

TSearchResult = TypeVar("TSearchResult")
TSearchOptions = TypeVar("TSearchOptions", bound="SearchOptions")


DEFAULT_RETURN_PARAMETER_METADATA: KernelParameterMetadata = KernelParameterMetadata(
    name="results",
    description="The search results.",
    type="list[str]",
    type_object=list,
    is_required=True,
)

DEFAULT_PARAMETER_METADATA: list[KernelParameterMetadata] = [
    KernelParameterMetadata(
        name="query",
        description="What to search for.",
        type="str",
        is_required=True,
        type_object=str,
    ),
    KernelParameterMetadata(
        name="top",
        description="Number of results to return.",
        type="int",
        is_required=False,
        default_value=2,
        type_object=int,
    ),
    KernelParameterMetadata(
        name="skip",
        description="Number of results to skip.",
        type="int",
        is_required=False,
        default_value=0,
        type_object=int,
    ),
]
DEFAULT_FUNCTION_NAME: Final[str] = "search"


@release_candidate
class SearchOptions(ABC, KernelBaseModel):
    """Options for a search.

    When multiple filters are used, they are combined with an AND operator.
    """

    filter: OptionalOneOrList[Callable | str] = None
    skip: Annotated[int, Field(ge=0)] = 0
    top: Annotated[int, Field(gt=0)] = 5
    include_total_count: bool = False

    model_config = ConfigDict(
        extra="allow", populate_by_name=True, arbitrary_types_allowed=True, validate_assignment=True
    )


@release_candidate
class KernelSearchResults(KernelBaseModel, Generic[TSearchResult]):
    """The result of a kernel search."""

    results: AsyncIterable[TSearchResult]
    total_count: int | None = None
    metadata: Mapping[str, Any] | None = None


class DynamicFilterFunction(Protocol):
    """Type definition for the filter update function in Text Search."""

    def __call__(
        self,
        filter: OptionalOneOrList[Callable | str] | None = None,
        parameters: list["KernelParameterMetadata"] | None = None,
        **kwargs: Any,
    ) -> OptionalOneOrList[Callable | str] | None:
        """Signature of the function."""
        ...  # pragma: no cover


def create_options(
    options_class: type["TSearchOptions"],
    options: SearchOptions | None,
    logger: Logger | None = None,
    **kwargs: Any,
) -> "TSearchOptions":
    """Create search options.

    If options are supplied, they are checked for the right type, and the kwargs are used to update the options.

    If options are not supplied, they are created from the kwargs.
    If that fails, an empty options object is returned.

    Args:
        options_class: The class of the options.
        options: The existing options to update.
        logger: The logger to use for warnings.
        **kwargs: The keyword arguments to use to create the options.

    Returns:
        The options of type options_class.

    Raises:
        ValidationError: If the options are not valid.

    """
    # no options give, so just try to create from kwargs
    if not options:
        return options_class.model_validate(kwargs)
    # options are the right class, just update based on kwargs
    if not isinstance(options, options_class):
        # options are not the right class, so create new options
        # first try to dump the existing, if this doesn't work for some reason, try with kwargs only
        additional_kwargs = {}
        try:
            additional_kwargs = options.model_dump(exclude_none=True, exclude_defaults=True, exclude_unset=True)
        except Exception:
            # This is very unlikely to happen, but if it does, we will just create new options.
            # one reason this could happen is if a different class is passed that has no model_dump method
            if logger:
                logger.warning("Options are not valid. Creating new options from just kwargs.")
        kwargs.update(additional_kwargs)
        return options_class.model_validate(kwargs)

    for key, value in kwargs.items():
        if key in options.__class__.model_fields:
            setattr(options, key, value)
    return options


def default_dynamic_filter_function(
    filter: OptionalOneOrList[Callable | str] | None = None,
    parameters: list["KernelParameterMetadata"] | None = None,
    **kwargs: Any,
) -> OptionalOneOrList[Callable | str] | None:
    """The default options update function.

    This function is used to update the query and options with the kwargs.
    You can supply your own version of this function to customize the behavior.

    Args:
        filter: The filter to use for the search.
        parameters: The parameters to use to create the options.
        **kwargs: The keyword arguments to use to update the options.

    Returns:
        OptionalOneOrList[Callable | str] | None: The updated filters

    """
    for param in parameters or []:
        assert param.name  # nosec, when used param name is always set
        if param.name in {"query", "top", "skip", "include_total_count"}:
            continue
        new_filter = None
        if param.name in kwargs:
            new_filter = f"lambda x: x.{param.name} == '{kwargs[param.name]}'"
        elif param.default_value:
            new_filter = f"lambda x: x.{param.name} == '{param.default_value}'"
        if not new_filter:
            continue
        if filter is None:
            filter = new_filter
        elif isinstance(filter, list):
            filter.append(new_filter)
        else:
            filter = [filter, new_filter]

    return filter
