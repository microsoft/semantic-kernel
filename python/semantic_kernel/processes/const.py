# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

END_PROCESS_ID: str = "Microsoft.SemanticKernel.Process.EndStep"


class ProcessSupportedComponents(str, Enum):
    """Supported Process Components."""

    Step = "Step"
    Process = "Process"
