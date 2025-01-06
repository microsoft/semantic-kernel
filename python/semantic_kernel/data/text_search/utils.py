# Copyright (c) Microsoft. All rights reserved.

import logging
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import ValidationError

if TYPE_CHECKING:
    from semantic_kernel.data.search_options import SearchOptions
    from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata

logger = logging.getLogger(__name__)


class OptionsUpdateFunctionType(Protocol):
    """Type definition for the options update function in Text Search."""

    def __call__(
        self,
        query: str,
        options: "SearchOptions",
        parameters: list["KernelParameterMetadata"] | None = None,
        **kwargs: Any,
    ) -> tuple[str, "SearchOptions"]:
        """Signature of the function."""
        ...  # pragma: no cover


def create_options(
    options_class: type["SearchOptions"],
    options: "SearchOptions | None",
    **kwargs: Any,
) -> "SearchOptions":
    """Create search options.

    If options are supplied, they are checked for the right type, and the kwargs are used to update the options.

    If options are not supplied, they are created from the kwargs.
    If that fails, an empty options object is returned.

    Args:
        options_class: The class of the options.
        options: The existing options to update.
        **kwargs: The keyword arguments to use to create the options.

    Returns:
        SearchOptions: The options.

    """
    new_options = options_class()
    if options:
        if not isinstance(options, options_class):
            inputs = None
            try:
                inputs = options.model_dump(exclude_none=True, exclude_defaults=True, exclude_unset=True)
            except Exception:
                logger.warning("Options are not valid. Creating new options.")
            if inputs:
                new_options = options_class.model_validate(inputs)
        else:
            new_options = options
        for key, value in kwargs.items():
            if key in new_options.model_fields:
                setattr(new_options, key, value)
    else:
        with suppress(ValidationError):
            new_options = options_class(**kwargs)
    return new_options


def default_options_update_function(
    query: str, options: "SearchOptions", parameters: list["KernelParameterMetadata"] | None = None, **kwargs: Any
) -> tuple[str, "SearchOptions"]:
    """The default options update function.

    This function is used to update the query and options with the kwargs.
    You can supply your own version of this function to customize the behavior.

    Args:
        query: The query.
        options: The options.
        parameters: The parameters to use to create the options.
        **kwargs: The keyword arguments to use to update the options.

    Returns:
        tuple[str, SearchOptions]: The updated query and options

    """
    for param in parameters or []:
        assert param.name  # nosec, when used param name is always set
        if param.name in {"query", "top", "skip"}:
            continue
        if param.name in kwargs:
            options.filter.equal_to(param.name, kwargs[param.name])
        if param.default_value:
            options.filter.equal_to(param.name, param.default_value)

    return query, options
