# Copyright (c) Microsoft. All rights reserved.

"""OpenAI Batch API implementation of the shared batch interface.

``OpenAIBatchMixin`` implements ``SupportsBatch`` against the ``AsyncOpenAI``
client a service already holds (``OpenAIHandler.client``), using the OpenAI
files+batches endpoints (``/v1/chat/completions`` in v1). Requests are encoded
to JSONL, uploaded via the files API, submitted with ``batches.create`` and
reconciled per-request — including explicit results for unrun (expired) and
cancelled requests rather than silently dropping them.
"""

import json
import logging
from io import BytesIO
from typing import Any

from semantic_kernel.connectors.batch_types import (
    Batch,
    BatchJob,
    BatchRequestResult,
    BatchStatus,
    SupportsBatch,
)
from semantic_kernel.exceptions import ServiceInvalidRequestError, ServiceResponseException

logger: logging.Logger = logging.getLogger(__name__)

_OPENAI_BATCH_ENDPOINT = "/v1/chat/completions"
_OPENAI_COMPLETION_WINDOW = "24h"

_OPENAI_STATUS_MAP = {
    "validating": BatchStatus.VALIDATING,
    "in_progress": BatchStatus.IN_PROGRESS,
    "finalizing": BatchStatus.FINALIZING,
    "completed": BatchStatus.COMPLETED,
    "failed": BatchStatus.FAILED,
    "expired": BatchStatus.EXPIRED,
    "cancelled": BatchStatus.CANCELLED,
    "cancelling": BatchStatus.CANCELLING,
}

# Lower number wins when merging multi-credential jobs.
_STATUS_SEVERITY = {
    BatchStatus.FAILED: 0,
    BatchStatus.EXPIRED: 1,
    BatchStatus.CANCELLED: 2,
    BatchStatus.IN_PROGRESS: 3,
    BatchStatus.VALIDATING: 3,
    BatchStatus.FINALIZING: 3,
    BatchStatus.CANCELLING: 3,
    BatchStatus.COMPLETED: 4,
}


def open_ai_batch_encode(requests: list[dict[str, Any]], endpoint: str = _OPENAI_BATCH_ENDPOINT) -> Batch:
    """Build a ``Batch`` of OpenAI payloads.

    Args:
        requests: One ``{"custom_id": str, "body": dict}`` entry per request.
            ``body`` is the same dict a normal ``chat.completions.create``
            call would take (``model``, ``messages``, …). An optional
            ``credential_key`` groups requests that must share a credential.
        endpoint: The batch endpoint path; defaults to chat completions.

    Returns:
        The encoded ``Batch`` ready for ``create_batch``.
    """
    from semantic_kernel.connectors.batch_types import BatchRequest

    return Batch(
        requests=[
            BatchRequest(
                custom_id=entry["custom_id"],
                endpoint=endpoint,
                payload=entry["body"],
                credential_key=entry.get("credential_key", "default"),
            )
            for entry in requests
        ]
    )


class OpenAIBatchMixin(SupportsBatch):
    """Implements ``SupportsBatch`` on services backed by ``AsyncOpenAI``.

    Mixed into ``OpenAIChatCompletion``; usable on any class exposing an
    ``AsyncOpenAI``-compatible ``.client``.
    """

    def batch_encode(self, requests: list[dict[str, Any]]) -> Batch:
        """Encode ``{"custom_id", "body"[, "credential_key"]}`` entries into a ``Batch``."""
        return open_ai_batch_encode(requests)

    async def create_batch(self, batch: Batch) -> BatchJob:
        """Encode, upload and submit the batch; returns the created job.

        Requests with different ``credential_key`` values are never mixed:
        each credential group is submitted as its own provider batch job and
        the provider ids are joined with ``+`` on the returned ``BatchJob``.
        """
        groups = batch.grouped_by_credential()
        if not groups:
            raise ServiceInvalidRequestError("Cannot create a batch job with zero requests.")

        job_ids: list[str] = []
        request_ids: list[str] = []
        status = BatchStatus.VALIDATING
        for group in groups.values():
            encoded = group.encode()
            try:
                uploaded = await self.client.files.create(  # type: ignore[attr-defined]
                    file=("batch_requests.jsonl", BytesIO(encoded), "application/jsonl"),
                    purpose="batch",
                )
                created = await self.client.batches.create(  # type: ignore[attr-defined]
                    input_file_id=uploaded.id,
                    endpoint=_OPENAI_BATCH_ENDPOINT,
                    completion_window=_OPENAI_COMPLETION_WINDOW,
                )
            except Exception as ex:
                raise ServiceResponseException(
                    f"{type(self)} failed to submit a batch job",
                    ex,
                ) from ex
            job_ids.append(created.id)
            request_ids.extend(request.custom_id for request in group.requests)
            status = _OPENAI_STATUS_MAP.get(created.status, BatchStatus.VALIDATING)

        return BatchJob(job_id="+".join(job_ids), status=status, request_ids=request_ids)

    async def get_batch_status(self, job: BatchJob) -> BatchJob:
        """Refresh status; multi-credential jobs report the aggregate."""
        provider_jobs = await self._retrieve_all(job)
        return self._merge_jobs(job.job_id, provider_jobs, job.request_ids)

    async def cancel_batch(self, job: BatchJob) -> BatchJob:
        """Cancel the job and return its updated state."""
        provider_jobs = []
        for job_id in job.job_id.split("+"):
            try:
                provider_jobs.append(await self.client.batches.cancel(job_id))  # type: ignore[attr-defined]
            except Exception as ex:
                raise ServiceResponseException(
                    f"{type(self)} failed to cancel batch {job_id}",
                    ex,
                ) from ex
        return self._merge_jobs(job.job_id, provider_jobs, job.request_ids)

    async def get_batch_results(self, job: BatchJob) -> list[BatchRequestResult]:
        """Per-request results, including explicit unrun/cancelled entries.

        Requests in ``job.request_ids`` that produced no output (expired
        before running, or dropped by a cancelled job) are reported with an
        explicit ``error`` instead of being silently omitted.
        """
        provider_jobs = await self._retrieve_all(job)
        results: dict[str, BatchRequestResult] = {}

        for provider_job in provider_jobs:
            status = _OPENAI_STATUS_MAP.get(provider_job.status, BatchStatus.FAILED)
            if provider_job.output_file_id:
                content = await self.client.files.content(provider_job.output_file_id)  # type: ignore[attr-defined]
                for line in content.text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    custom_id = entry.get("custom_id", "")
                    response = entry.get("response") or {}
                    error = entry.get("error")
                    results[custom_id] = BatchRequestResult(
                        custom_id=custom_id,
                        status_code=response.get("status_code"),
                        response=response.get("body") if error is None else None,
                        error=json.dumps(error) if error else None,
                    )

            if status == BatchStatus.EXPIRED:
                expired = getattr(provider_job, "expired_requests", None) or {}
                expired_ids = set(expired.get("requests") or []) if isinstance(expired, dict) else set()
                for expired_id in expired_ids:
                    results[expired_id] = BatchRequestResult(
                        custom_id=expired_id,
                        error="request expired before it ran",
                    )

        if job.request_ids:
            for custom_id in job.request_ids:
                if custom_id not in results:
                    aggregate = self._merge_jobs(job.job_id, provider_jobs, job.request_ids)
                    placeholder = (
                        "request did not run (job expired)"
                        if aggregate.status == BatchStatus.EXPIRED
                        else "request did not run (job cancelled or result unavailable)"
                    )
                    results[custom_id] = BatchRequestResult(custom_id=custom_id, error=placeholder)

        return [results[custom_id] for custom_id in job.request_ids] if job.request_ids else list(results.values())

    async def _retrieve_all(self, job: BatchJob):
        provider_jobs = []
        for job_id in job.job_id.split("+"):
            try:
                provider_jobs.append(await self.client.batches.retrieve(job_id))  # type: ignore[attr-defined]
            except Exception as ex:
                raise ServiceResponseException(
                    f"{type(self)} failed to retrieve batch {job_id}",
                    ex,
                ) from ex
        return provider_jobs

    def _merge_jobs(self, job_id: str, provider_jobs, request_ids: list[str]) -> BatchJob:
        """Merge several provider jobs (one per credential group) into one."""
        counts: dict[str, int] = {}
        merged_status = BatchStatus.COMPLETED
        error = None
        for provider_job in provider_jobs:
            status = _OPENAI_STATUS_MAP.get(provider_job.status, BatchStatus.FAILED)
            if _STATUS_SEVERITY.get(status, 0) < _STATUS_SEVERITY.get(merged_status, 4):
                merged_status = status
            request_counts = getattr(provider_job, "request_counts", None)
            if request_counts:
                for key in ("total", "completed", "failed"):
                    counts[key] = counts.get(key, 0) + (getattr(request_counts, key, 0) or 0)
            errors = getattr(provider_job, "errors", None)
            if errors and getattr(errors, "data", None):
                error = "; ".join(e.message for e in errors.data if getattr(e, "message", None))
        return BatchJob(
            job_id=job_id,
            status=merged_status,
            request_counts=counts,
            request_ids=list(request_ids),
            error=error,
        )
