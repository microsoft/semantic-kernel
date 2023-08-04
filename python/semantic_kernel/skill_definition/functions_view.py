# Copyright (c) Microsoft. All rights reserved.

from typing import Dict, List

import pydantic as pdt

from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.skill_definition.function_view import FunctionView


class FunctionsView(SKBaseModel):
    semantic_functions: Dict[str, List[FunctionView]] = pdt.Field(default_factory=dict)
    native_functions: Dict[str, List[FunctionView]] = pdt.Field(default_factory=dict)

    def add_function(self, view: FunctionView) -> "FunctionsView":
        if view.is_semantic:
            if view.skill_name not in self.semantic_functions:
                self.semantic_functions[view.skill_name] = []
            self.semantic_functions[view.skill_name].append(view)
        else:
            if view.skill_name not in self.native_functions:
                self.native_functions[view.skill_name] = []
            self.native_functions[view.skill_name].append(view)

        return self

    def is_semantic(self, skill_name: str, function_name: str) -> bool:
        as_sf = self.semantic_functions.get(skill_name, [])
        as_sf = any(f.name == function_name for f in as_sf)

        as_nf = self.native_functions.get(skill_name, [])
        as_nf = any(f.name == function_name for f in as_nf)

        if as_sf and as_nf:
            raise KernelException(
                KernelException.ErrorCodes.AmbiguousImplementation,
                (
                    f"There are 2 functions with the same name: {function_name}."
                    "One is native and the other semantic."
                ),
            )

        return as_sf

    def is_native(self, skill_name: str, function_name: str) -> bool:
        as_sf = self.semantic_functions.get(skill_name, [])
        as_sf = any(f.name == function_name for f in as_sf)

        as_nf = self.native_functions.get(skill_name, [])
        as_nf = any(f.name == function_name for f in as_nf)

        if as_sf and as_nf:
            raise KernelException(
                KernelException.ErrorCodes.AmbiguousImplementation,
                (
                    f"There are 2 functions with the same name: {function_name}."
                    "One is native and the other semantic."
                ),
            )

        return as_nf
