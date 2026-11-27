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

from pydantic import ValidationError

from semantic_kernel.connectors.batch_types import (
    Batch,
    BatchJob,
    BatchRequest,
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

# Only applied once every child job is terminal; lower number wins.
_TERMINAL_SEVERITY = {
    BatchStatus.FAILED: 0,
    BatchStatus.EXPIRED: 1,
    BatchStatus.CANCELLED: 2,
    BatchStatus.COMPLETED: 3,
}

# While any child is still active the aggregate must stay non-terminal, or a
# caller polling on is_terminal would stop early and collect partial results.
_ACTIVE_SEVERITY = {
    BatchStatus.FINALIZING: 0,
    BatchStatus.IN_PROGRESS: 1,
    BatchStatus.VALIDATING: 2,
    BatchStatus.CANCELLING: 3,
}


def open_ai_batch_encode(requests: list[dict[str, Any]], endpoint: str = _OPENAI_BATCH_ENDPOINT) -> Batch:
    """Build a ``Batch`` of OpenAI payloads.

    Args:
        requests: One ``{"custom_id": str, "body": dict}`` entry per request.
            ``body`` is the same dict a normal ``chat.completions.create``
            call would take (``model``, ``messages``, …). An optional
            ``credential_key`` groups requests that must share a credential.
        endpoint: The batch endpoint path applied to every request; defaults
            to chat completions.

    Returns:
        The encoded ``Batch`` ready for ``create_batch``.

    Raises:
        ServiceInvalidRequestError: When an entry is missing ``custom_id`` or
            ``body``, or carries values that cannot form a ``BatchRequest``.
    """
    encoded = []
    for index, entry in enumerate(requests):
        try:
            encoded.append(
                BatchRequest(
                    custom_id=entry["custom_id"],
                    endpoint=endpoint,
                    payload=entry["body"],
                    credential_key=entry.get("credential_key", "default"),
                )
            )
        except (KeyError, TypeError) as ex:
            raise ServiceInvalidRequestError(
                f"Batch entry #{index} is malformed (needs 'custom_id' and 'body'): {entry!r}"
            ) from ex
        except ValidationError as ex:
            raise ServiceInvalidRequestError(f"Batch entry #{index} has invalid fields: {ex}") from ex
    return Batch(requests=encoded)


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
        When a later group fails to submit, earlier provider jobs are cancelled
        best-effort so no untracked work keeps running (and billing) behind
        the caller's back.
        """
        if not batch.requests:
            raise ServiceInvalidRequestError("Cannot create a batch job with zero requests.")

        seen: set[str] = set()
        duplicates = sorted({
            request.custom_id for request in batch.requests if request.custom_id in seen or seen.add(request.custom_id)
        })
        if duplicates:
            raise ServiceInvalidRequestError(f"Duplicate custom_id values in batch: {', '.join(duplicates)}")

        endpoints = {request.endpoint for request in batch.requests}
        if len(endpoints) != 1:
            raise ServiceInvalidRequestError(
                f"All requests in one provider batch must share an endpoint, got {sorted(endpoints)}"
            )

        groups = batch.grouped_by_credential()
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
                    endpoint=group.requests[0].endpoint,
                    completion_window=_OPENAI_COMPLETION_WINDOW,
                )
            except Exception as ex:
                cleanup_note = ""
                if job_ids:
                    cancelled, cancel_failed = await self._cancel_submitted_quietly(job_ids)
                    parts = []
                    if cancelled:
                        parts.append(f"cancellation requested for already-submitted jobs {cancelled}")
                    if cancel_failed:
                        # Surface the ids whose cancel call itself failed so
                        # the caller can retry via cancel_batch — these jobs
                        # may still be running (and billing) on the provider.
                        parts.append(f"could NOT be cancelled, still running — retry via cancel_batch: {cancel_failed}")
                    cleanup_note = f" ({'; '.join(parts)})" if parts else ""
                raise ServiceResponseException(
                    f"{type(self)} failed to submit a batch job{cleanup_note}",
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
        """Per-request results for a finished job.

        Every provider job must be terminal before collection — while any
        child is still validating/running/finalizing, this raises
        ``ServiceInvalidRequestError`` rather than fabricating "did not run"
        results for work still in flight.

        Requests in ``job.request_ids`` that produced no output (expired
        before running, or dropped by a cancelled job) are reported with an
        explicit ``error`` instead of being silently omitted.
        """
        provider_jobs = await self._retrieve_all(job)
        if not provider_jobs:
            raise ServiceInvalidRequestError(f"No provider jobs found for {job.job_id!r}")
        pending = [
            pj.id for pj in provider_jobs if not _OPENAI_STATUS_MAP.get(pj.status, BatchStatus.FAILED).is_terminal
        ]
        if pending:
            raise ServiceInvalidRequestError(
                f"Batch job(s) {pending} are still running; collect results only after they finish."
            )

        results: dict[str, BatchRequestResult] = {}
        for provider_job in provider_jobs:
            status = _OPENAI_STATUS_MAP.get(provider_job.status, BatchStatus.FAILED)
            for file_id, is_error_file in (
                (getattr(provider_job, "output_file_id", None), False),
                (getattr(provider_job, "error_file_id", None), True),
            ):
                if not file_id:
                    continue
                try:
                    content = await self.client.files.content(file_id)  # type: ignore[attr-defined]
                except Exception as ex:
                    kind = "error" if is_error_file else "output"
                    raise ServiceResponseException(
                        f"{type(self)} failed to download batch {kind} file {file_id}",
                        ex,
                    ) from ex
                for line in content.text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    custom_id = entry.get("custom_id", "")
                    response = entry.get("response") or {}
                    error = entry.get("error")
                    status_code = response.get("status_code")
                    body = response.get("body")
                    if error is None and isinstance(status_code, int) and status_code >= 400:
                        # The provider ran the request and got an HTTP error;
                        # the body is an error payload, not a usable result.
                        error = body if body is not None else {"code": status_code}
                        body = None
                    results[custom_id] = BatchRequestResult(
                        custom_id=custom_id,
                        status_code=status_code,
                        response=body if error is None else None,
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
            aggregate = self._merge_jobs(job.job_id, provider_jobs, job.request_ids)
            placeholder = (
                "request did not run (job expired)"
                if aggregate.status == BatchStatus.EXPIRED
                else "request did not run (job cancelled or result unavailable)"
            )
            for custom_id in job.request_ids:
                if custom_id not in results:
                    results[custom_id] = BatchRequestResult(custom_id=custom_id, error=placeholder)
            return [results[custom_id] for custom_id in job.request_ids]
        return list(results.values())

    async def _cancel_submitted_quietly(self, job_ids: list[str]) -> tuple[list[str], list[str]]:
        """Best-effort cancel of already-submitted provider jobs on partial failure.

        Returns:
            A ``(cancelled, failed)`` pair of provider job ids: ``cancelled``
            received the cancel request, ``failed`` are the ids whose cancel
            call itself errored and may still be running — the caller surfaces
            them so they can be retried via ``cancel_batch``.
        """
        cancelled: list[str] = []
        failed: list[str] = []
        for job_id in job_ids:
            try:
                await self.client.batches.cancel(job_id)  # type: ignore[attr-defined]
                cancelled.append(job_id)
            except Exception:
                logger.warning("Failed to cancel provider batch job %s after a partial submission failure", job_id)
                failed.append(job_id)
        return cancelled, failed

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
        """Merge several provider jobs (one per credential group) into one.

        The aggregate stays non-terminal while any child is still running so
        polling never finishes early; once every child is terminal the worst
        terminal state wins (failed > expired > cancelled > completed).
        """
        counts: dict[str, int] = {}
        error = None
        statuses = [_OPENAI_STATUS_MAP.get(pj.status, BatchStatus.FAILED) for pj in provider_jobs]
        if all(status.is_terminal for status in statuses):
            merged_status = min(statuses, key=lambda s: _TERMINAL_SEVERITY.get(s, 99), default=BatchStatus.COMPLETED)
        else:
            merged_status = min(statuses, key=lambda s: _ACTIVE_SEVERITY.get(s, 99), default=BatchStatus.IN_PROGRESS)
        for provider_job in provider_jobs:
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
