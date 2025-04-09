# Copyright (c) Microsoft. All rights reserved.
from typing import TYPE_CHECKING, ClassVar

from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.process_step_builder import ProcessStepBuilder
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.functions import KernelFunctionMetadata
    from semantic_kernel.kernel import Kernel


@experimental
class EndStep(ProcessStepBuilder):
    """An end step in a process."""

    END_STEP_VALUE: ClassVar[str] = "Microsoft.SemanticKernel.Process.EndStep"
    END_STEP_NAME: ClassVar[str] = END_STEP_VALUE
    END_STEP_ID: ClassVar[str] = END_STEP_VALUE

    @staticmethod
    def get_instance() -> "EndStep":
        """Get the instance of the end step."""
        return EndStep()

    def __init__(self):
        """Initialize the end step."""
        super().__init__(
            name=self.END_STEP_VALUE,
        )

    def get_function_metadata_map(
        self, plugin_type, name: str | None = None, kernel: "Kernel | None" = None
    ) -> dict[str, "KernelFunctionMetadata"]:
        """Gets the function metadata map."""
        return {}

    def build_step(self) -> KernelProcessStepInfo:
        """Build the step."""
        return KernelProcessStepInfo(
            inner_step_type=KernelProcessStepState,
            state=KernelProcessStepState(name=self.END_STEP_NAME),
            output_edges={},
        )
