# Copyright (c) Microsoft. All rights reserved.

"""Provider-independent types for provider Batch APIs.

These types give Semantic Kernel connectors a shared way to describe batch
requests (``BatchRequest``), group them (``Batch``), track a submitted batch
job (``BatchJob`` / ``BatchStatus``), and read per-request results including
unrun or cancelled requests (``BatchRequestResult``).

Provider Batch APIs run the same calls asynchronously, typically at a lower
price and within a bounded completion window. The shared abstraction keeps
grouping, polling and error semantics consistent across connectors instead of
ad-hoc per-connector chunking.

This is a new opt-in API surface; no existing non-batch paths change.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class BatchStatus(str, Enum):
    """Lifecycle states of a provider batch job."""

    VALIDATING = "validating"
    IN_PROGRESS = "in_progress"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    CANCELLING = "cancelling"

    @property
    def is_terminal(self) -> bool:
        """Whether the job reached a state where no more requests will run."""
        return self in {
            BatchStatus.COMPLETED,
            BatchStatus.FAILED,
            BatchStatus.EXPIRED,
            BatchStatus.CANCELLED,
        }


class BatchRequest(KernelBaseModel):
    """A single unit of work inside a provider batch job.

    ``credential_key`` groups requests that must share a provider credential;
    only requests with the same key are submitted in one job.
    """

    custom_id: str
    """Stable identifier echoed back with the per-request result."""
    endpoint: str
    """Provider endpoint for this request, e.g. ``/v1/chat/completions``."""
    payload: dict[str, Any]
    """Provider-native request body (the ``body`` of a batch API request line)."""
    credential_key: str = "default"
    """Grouping key; batch creation never mixes different credential keys."""


class Batch(KernelBaseModel):
    """An encoded batch of requests plus helpers for grouping and encoding."""

    requests: list[BatchRequest] = Field(default_factory=list)

    def encode(self) -> bytes:
        """Encode the requests as JSON Lines, one provider payload per line."""
        import json

        return "".join(
            json.dumps({
                "custom_id": request.custom_id,
                "method": "POST",
                "url": request.endpoint,
                "body": request.payload,
            })
            + "\n"
            for request in self.requests
        ).encode()

    def grouped_by_credential(self) -> dict[str, "Batch"]:
        """Split the batch into one batch per credential key, preserving order."""
        groups: dict[str, list[BatchRequest]] = {}
        for request in self.requests:
            groups.setdefault(request.credential_key, []).append(request)
        return {key: type(self)(requests=items) for key, items in groups.items()}


class BatchJob(KernelBaseModel):
    """A submitted provider batch job and its current status."""

    job_id: str
    """Provider-side batch identifier (multi-credential submissions join ids with ``+``)."""
    status: BatchStatus = BatchStatus.VALIDATING
    """Latest known lifecycle state."""
    request_counts: dict[str, int] = Field(default_factory=dict)
    """Provider-reported counters, e.g. ``{"total": 10, "completed": 4, "failed": 1}``."""
    request_ids: list[str] = Field(default_factory=list)
    """The ``custom_id``s submitted with this job; used to report unrun/cancelled requests."""
    error: str | None = None
    """Top-level job error when the job itself failed."""


class BatchRequestResult(KernelBaseModel):
    """The outcome of one ``BatchRequest`` inside a finished job."""

    custom_id: str
    """The ``BatchRequest.custom_id`` this result answers."""
    status_code: int | None = None
    """HTTP status code of the per-request response, when it ran."""
    response: dict[str, Any] | None = None
    """Provider-native response body, when the request ran."""
    error: str | None = None
    """Error detail when the request failed, expired unrun, or was cancelled."""

    @property
    def succeeded(self) -> bool:
        """Whether the request produced a usable response.

        When the provider reports an HTTP status for the request, it must be a
        successful one; error bodies with failing status codes are not usable
        results even when the provider still returns a body.
        """
        if self.error is not None or self.response is None:
            return False
        return not (self.status_code is not None and self.status_code >= 400)


class SupportsBatch(ABC):
    """Opt-in interface for services that can submit provider batch jobs.

    Implementations encode ``BatchRequest`` items into the provider's batch
    request format, submit them grouped by ``credential_key``, and report
    per-request results. Methods raise ``ServiceResponseException`` on provider
    errors and ``ServiceInvalidRequestError`` for malformed input.
    """

    @abstractmethod
    def batch_encode(self, requests: list[dict[str, Any]]) -> "Batch":
        """Encode raw request entries into this provider's ``Batch`` format."""
        raise NotImplementedError

    @abstractmethod
    async def create_batch(self, batch: Batch) -> BatchJob:
        """Submit the batch to the provider and return the created job."""
        raise NotImplementedError

    @abstractmethod
    async def get_batch_status(self, job: BatchJob) -> BatchJob:
        """Refresh and return the job's status."""
        raise NotImplementedError

    @abstractmethod
    async def cancel_batch(self, job: BatchJob) -> BatchJob:
        """Request cancellation of the job and return its updated state."""
        raise NotImplementedError

    @abstractmethod
    async def get_batch_results(self, job: BatchJob) -> list[BatchRequestResult]:
        """Return per-request results for a completed job.

        Includes explicit entries for unrun (expired) and cancelled requests
        rather than silently dropping them.
        """
        raise NotImplementedError
