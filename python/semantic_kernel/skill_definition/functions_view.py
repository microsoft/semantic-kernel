# Copyright (c) Microsoft. All rights reserved.

from typing import Dict, List

from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.skill_definition.function_view import FunctionView


class FunctionsView:
    _semantic_functions: Dict[str, List[FunctionView]]
    _native_functions: Dict[str, List[FunctionView]]

    def __init__(self) -> None:
        self._semantic_functions = {}
        self._native_functions = {}

    def add_function(self, view: FunctionView) -> "FunctionsView":
        if view.is_semantic:
            if view.skill_name not in self._semantic_functions:
                self._semantic_functions[view.skill_name] = []
            self._semantic_functions[view.skill_name].append(view)
        else:
            if view.skill_name not in self._native_functions:
                self._native_functions[view.skill_name] = []
            self._native_functions[view.skill_name].append(view)

        return self

    def is_semantic(self, skill_name: str, function_name: str) -> bool:
        as_sf = self._semantic_functions.get(skill_name, [])
        as_sf = any(f.name == function_name for f in as_sf)

        as_nf = self._native_functions.get(skill_name, [])
        as_nf = any(f.name == function_name for f in as_nf)

        if as_sf and as_nf:
            raise KernelException(
                KernelException.ErrorCodes.AmbiguousImplementation,
                f"There are 2 functions with the same name: {function_name}."
                f"One is native and the other semantic.",
            )

        return as_sf

    def is_native(self, skill_name: str, function_name: str) -> bool:
        return not self.is_semantic(skill_name, function_name)
