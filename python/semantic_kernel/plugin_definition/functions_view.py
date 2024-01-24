# Copyright (c) Microsoft. All rights reserved.

from typing import Dict, List

from pydantic import Field

from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.plugin_definition.function_view import FunctionView


class FunctionsView(KernelBaseModel):
    semantic_functions: Dict[str, List[FunctionView]] = Field(default_factory=dict)
    native_functions: Dict[str, List[FunctionView]] = Field(default_factory=dict)

    def add_function(self, view: FunctionView) -> "FunctionsView":
        if view.is_semantic:
            if view.plugin_name not in self.semantic_functions:
                self.semantic_functions[view.plugin_name] = []
            self.semantic_functions[view.plugin_name].append(view)
        else:
            if view.plugin_name not in self.native_functions:
                self.native_functions[view.plugin_name] = []
            self.native_functions[view.plugin_name].append(view)

        return self

    def is_semantic(self, plugin_name: str, function_name: str) -> bool:
        as_sf = self.semantic_functions.get(plugin_name, [])
        as_sf = any(f.name == function_name for f in as_sf)

        as_nf = self.native_functions.get(plugin_name, [])
        as_nf = any(f.name == function_name for f in as_nf)

        if as_sf and as_nf:
            raise KernelException(
                KernelException.ErrorCodes.AmbiguousImplementation,
                (f"There are 2 functions with the same name: {function_name}." "One is native and the other semantic."),
            )

        return as_sf

    def is_native(self, plugin_name: str, function_name: str) -> bool:
        as_sf = self.semantic_functions.get(plugin_name, [])
        as_sf = any(f.name == function_name for f in as_sf)

        as_nf = self.native_functions.get(plugin_name, [])
        as_nf = any(f.name == function_name for f in as_nf)

        if as_sf and as_nf:
            raise KernelException(
                KernelException.ErrorCodes.AmbiguousImplementation,
                (f"There are 2 functions with the same name: {function_name}." "One is native and the other semantic."),
            )

        return as_nf
