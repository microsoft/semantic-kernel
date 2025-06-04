# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from semantic_kernel.utils.feature_stage_decorator import experimental

END_PROCESS_ID: str = "Microsoft.SemanticKernel.Process.EndStep"


@experimental
class ProcessSupportedComponents(str, Enum):
    """Supported Process Components."""

    Step = "Step"
    Process = "Process"
