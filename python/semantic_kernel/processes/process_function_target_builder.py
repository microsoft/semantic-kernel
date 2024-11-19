# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.processes.process_end_step import EndStep
from semantic_kernel.processes.process_step_builder import ProcessStepBuilder
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class ProcessFunctionTargetBuilder(KernelBaseModel):
    """A builder for a process function target."""

    step: ProcessStepBuilder
    function_name: str | None = None
    parameter_name: str | None = None
    target_event_id: str | None = None

    def __init__(
        self, step: ProcessStepBuilder, function_name: str | Enum | None = None, parameter_name: str | None = None
    ):
        """Initializes a new instance of ProcessFunctionTargetBuilder."""
        from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata  # noqa: F401

        ProcessFunctionTargetBuilder.model_rebuild()

        function_name_str: str | None = function_name.value if isinstance(function_name, Enum) else function_name

        if isinstance(step, EndStep):
            function_name_str = "END"
            parameter_name = None
        else:
            target = step.resolve_function_target(function_name_str, parameter_name)
            function_name_str = target.function_name
            parameter_name = target.parameter_name

        super().__init__(step=step, function_name=function_name_str, parameter_name=parameter_name)

    def build(self) -> KernelProcessFunctionTarget:
        """Builds the KernelProcessFunctionTarget."""
        if not self.step.id:
            raise ValueError("Step ID cannot be None")

        return KernelProcessFunctionTarget(
            step_id=self.step.id,
            function_name=self.function_name,
            parameter_name=self.parameter_name,
            target_event_id=self.target_event_id,
        )
