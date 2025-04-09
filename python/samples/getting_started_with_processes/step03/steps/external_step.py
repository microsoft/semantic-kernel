# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.processes.kernel_process.kernel_process_event import (
    KernelProcessEventVisibility,
)
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext


class ExternalStep(KernelProcessStep):
    def __init__(self, external_event_name: str):
        super().__init__(external_event_name=external_event_name)

    @kernel_function()
    async def emit_external_event(self, context: KernelProcessStepContext, data: Any):
        await context.emit_event(
            process_event=self.external_event_name, data=data, visibility=KernelProcessEventVisibility.Public
        )
