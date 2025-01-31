# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, Protocol

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

    Raises:
        ValidationError: If the options are not valid.

    """
    # no options give, so just try to create from kwargs
    if not options:
        return options_class.model_validate(kwargs)
    # options are the right class, just update based on kwargs
    if isinstance(options, options_class):
        for key, value in kwargs.items():
            if key in options.model_fields:
                setattr(options, key, value)
        return options
    # options are not the right class, so create new options
    # first try to dump the existing, if this doesn't work for some reason, try with kwargs only
    inputs = {}
    try:
        inputs = options.model_dump(exclude_none=True, exclude_defaults=True, exclude_unset=True)
    except Exception:
        # This is very unlikely to happen, but if it does, we will just create new options.
        # one reason this could happen is if a different class is passed that has no model_dump method
        logger.warning("Options are not valid. Creating new options from just kwargs.")
    inputs.update(kwargs)
    return options_class.model_validate(kwargs)


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
