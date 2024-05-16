# Copyright (c) Microsoft. All rights reserved.

from typing import Callable, Literal

from pydantic import Field

from semantic_kernel.filters.filter_context_base import FilterContextBase
from semantic_kernel.kernel_pydantic import KernelBaseModel

CALLABLE_FILTER_TYPE = Callable[[FilterContextBase, Callable[[FilterContextBase], None]], None]


ALLOWED_FILTERS = ["function_invocation", "prompt_rendering"]
FILTER_MAPPING = {
    "function_invocation": "function_invocation_filters",
    "prompt_rendering": "prompt_rendering_filters",
}


class KernelFilterExtension(KernelBaseModel):
    """KernelFilterExtension."""

    function_invocation_filters: list[tuple[int, CALLABLE_FILTER_TYPE]] = Field(default_factory=list)
    prompt_rendering_filters: list[tuple[int, CALLABLE_FILTER_TYPE]] = Field(default_factory=list)

    def add_filter(
        self, filter_type: Literal["function_invocation", "prompt_rendering"], filter: CALLABLE_FILTER_TYPE
    ) -> None:
        """Add a filter to the Kernel.

        Each filter is added to the beginning of the list of filters,
        this is because the filters are executed in the order they are added,
        so the first filter added, will be the first to be executed,
        but it will also be the last executed for the part after `await next(context)`.

        Args:
            filter_type (str): The type of the filter to add (function_invocation, prompt_rendering)
            filter (object): The filter to add

        """
        if filter_type not in ALLOWED_FILTERS:
            raise ValueError(f"filter_type must be one of {ALLOWED_FILTERS}")
        getattr(self, FILTER_MAPPING[filter_type]).insert(0, (id(filter), filter))

    def filter(
        self, filter_type: Literal["function_invocation", "prompt_rendering"]
    ) -> Callable[[CALLABLE_FILTER_TYPE], CALLABLE_FILTER_TYPE]:
        def decorator(
            func: CALLABLE_FILTER_TYPE,
        ) -> CALLABLE_FILTER_TYPE:
            self.add_filter(filter_type, func)
            return func

        return decorator

    def remove_filter(
        self,
        filter_type: Literal["function_invocation", "prompt_rendering"] | None = None,
        filter_id: int | None = None,
        position: int | None = None,
    ) -> None:
        """Remove a filter from the Kernel.

        Args:
            filter_type (str | None): The type of the filter to remove (function_invocation, prompt_render)
            filter_id (int): The id of the hook to remove
            position (int): The position of the filter in the list

        """
        if filter_id is None and position is None:
            raise ValueError("Either hook_id or position should be provided.")
        if position is not None:
            if filter_type is None:
                raise ValueError("Please specify the type of filter when using position.")
            getattr(self, FILTER_MAPPING[filter_type]).pop(position)
            return
        if filter_type:
            for f_id, _ in getattr(self, FILTER_MAPPING[filter_type]):
                if f_id == filter_id:
                    getattr(self, FILTER_MAPPING[filter_type]).remove((f_id, _))
                    return
        for filter_list in FILTER_MAPPING.values():
            for f_id, _ in getattr(self, filter_list):
                if f_id == filter_id:
                    getattr(self, filter_list).remove((f_id, _))
                    return
