# Copyright (c) Microsoft. All rights reserved.

from datetime import timedelta

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RunPollingOptions(KernelBaseModel):
    """Configuration and defaults associated with polling behavior for Assistant API requests."""

    default_polling_interval: timedelta = Field(default=timedelta(milliseconds=250))
    default_polling_backoff: timedelta = Field(default=timedelta(seconds=1))
    default_polling_backoff_threshold: int = Field(default=2)
    default_message_synchronization_delay: timedelta = Field(default=timedelta(milliseconds=250))
    run_polling_interval: timedelta = Field(default=timedelta(milliseconds=250))
    run_polling_backoff: timedelta = Field(default=timedelta(seconds=1))
    run_polling_backoff_threshold: int = Field(default=2)
    message_synchronization_delay: timedelta = Field(default=timedelta(milliseconds=250))
    run_polling_timeout: timedelta = Field(default=timedelta(minutes=1))  # New timeout attribute

    def get_polling_interval(self, iteration_count: int) -> timedelta:
        """Get the polling interval for the given iteration count."""
        return (
            self.run_polling_backoff
            if iteration_count > self.run_polling_backoff_threshold
            else self.run_polling_interval
        )
