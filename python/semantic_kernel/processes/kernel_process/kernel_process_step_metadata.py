# Copyright (c) Microsoft. All rights reserved.


class KernelProcessStepMetadataAttribute:
    """The metadata attribute for a Kernel Process Step."""

    def __init__(self, version: str = "v1"):
        """Initializes a new instance of the KernelProcessStepMetadataAttribute class."""
        self.version = version


def kernel_process_step_metadata(version: str = "v1"):
    """Decorator to attach metadata to a Kernel Process Step class.

    Example usage:
        @kernel_process_step_metadata("v2")
        class MyStep(KernelProcessStep[TState]):
            ...
    """

    def decorator(cls):
        setattr(cls, "_kernel_process_step_metadata", KernelProcessStepMetadataAttribute(version))
        return cls

    return decorator
