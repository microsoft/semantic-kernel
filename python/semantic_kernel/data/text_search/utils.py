# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import ValidationError

from semantic_kernel.data.search_options import SearchOptions
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


def create_options(
    options_class: type[SearchOptions],
    options: SearchOptions | None,
    parameters: list[KernelParameterMetadata] | None = None,
    parameter_aliases: dict[str, str] | None = None,
    **kwargs: Any,
) -> SearchOptions:
    """Create search options.

    If options are supplied, they are checked for the right type, and the kwargs are used to update the options.

    If options are not supplied, they are created from the kwargs.
    If that fails, an empty options object is returned.

    Args:
        options_class: The class of the options.
        options: The existing options to update.
        parameters: The parameters to use to create the options.
        parameter_aliases: The aliases to use for the parameters,
            for instance when a technical name of the filter is not a good name for the LLM to use.
            The key is the LLM name, should be in parameters, the value is the technical name.
        **kwargs: The keyword arguments to use to create the options.

    Returns:
        SearchOptions: The options.

    """
    if options:
        if not isinstance(options, options_class):
            try:
                # Validate the options in one go
                new_options = options_class.model_validate(
                    options.model_dump(exclude_none=True, exclude_defaults=True, exclude_unset=True),
                )
            except ValidationError:
                # if that fails, go one by one
                new_options = options_class()
                for key, value in options.model_dump(
                    exclude_none=True, exclude_defaults=True, exclude_unset=True
                ).items():
                    setattr(new_options, key, value)
        else:
            new_options = options
        for key, value in kwargs.items():
            if key in new_options.model_fields:
                setattr(new_options, key, value)
    else:
        try:
            new_options = options_class(**kwargs)
        except ValidationError:
            new_options = options_class()
    # treat non standard parameters as equality filter clauses
    if not parameters:
        return new_options
    for param in parameters:
        if param.name not in {"query", "top", "skip"} and param.name in kwargs:
            if parameter_aliases and param.name in parameter_aliases:
                new_options.filter.equal_to(parameter_aliases[param.name], kwargs[param.name])
            else:
                new_options.filter.equal_to(param.name, kwargs[param.name])

    return new_options
