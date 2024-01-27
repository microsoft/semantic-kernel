# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.events.kernel_events_args import KernelEventArgs


class FunctionInvokingEventArgs(KernelEventArgs):
    def __init__(self, function_view, context):
        super().__init__(function_view, context)
        self._skip_requested = False

    @property
    def is_skip_requested(self):
        return self._skip_requested

    def skip(self):
        self._skip_requested = True
