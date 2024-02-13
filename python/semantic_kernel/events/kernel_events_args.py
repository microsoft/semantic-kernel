# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.orchestration.kernel_context import KernelContext
from semantic_kernel.plugin_definition.function_view import FunctionView


class KernelEventArgs:
    def __init__(self, function_view: FunctionView, context: KernelContext):
        if context is None or function_view is None:
            raise ValueError("function_view and context cannot be None")

        self._function_view = function_view
        self._context = context

        # Temporal cancellationToken to sync C#
        self._is_cancel_requested = False

    @property
    def function_view(self):
        return self._function_view

    @property
    def context(self):
        return self._context

    @property
    def is_cancel_requested(self):
        return self._is_cancel_requested

    def cancel(self):
        self._is_cancel_requested = True
