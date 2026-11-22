# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from semantic_kernel.connectors.batch_types import (
    Batch,
    BatchJob,
    BatchRequest,
    BatchStatus,
    SupportsBatch,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_batch import (
    OpenAIBatchMixin,
    open_ai_batch_encode,
)
from semantic_kernel.exceptions import ServiceInvalidRequestError, ServiceResponseException


class _FakeBatchService(OpenAIBatchMixin):
    """Minimal service exposing an AsyncOpenAI-shaped client for the mixin."""

    def __init__(self):
        self.client = MagicMock()
        self.client.files = MagicMock()
        self.client.batches = MagicMock()
        self.client.files.create = AsyncMock()
        self.client.files.content = AsyncMock()
        self.client.batches.create = AsyncMock()
        self.client.batches.retrieve = AsyncMock()
        self.client.batches.cancel = AsyncMock()


def _service():
    return _FakeBatchService()


def _provider_job(**kwargs):
    job = MagicMock()
    job.id = kwargs.get("id", "batch_abc")
    job.status = kwargs.get("status", "completed")
    job.output_file_id = kwargs.get("output_file_id", "file-out")
    job.error_file_id = kwargs.get("error_file_id")
    job.expired_requests = kwargs.get("expired_requests")
    job.errors = kwargs.get("errors")
    request_counts = MagicMock()
    request_counts.total = kwargs.get("total", 2)
    request_counts.completed = kwargs.get("completed", 2)
    request_counts.failed = kwargs.get("failed", 0)
    job.request_counts = request_counts
    return job


def test_mixin_implements_supports_batch():
    assert isinstance(_service(), SupportsBatch)


def test_encode_produces_provider_payloads():
    batch = open_ai_batch_encode(
        [
            {"custom_id": "r1", "body": {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]}},
            {"custom_id": "r2", "body": {"model": "gpt-4o-mini", "messages": []}},
        ]
    )
    encoded = batch.encode().decode()
    lines = [json.loads(line) for line in encoded.strip().splitlines()]
    assert len(lines) == 2
    assert lines[0]["custom_id"] == "r1"
    assert lines[0]["url"] == "/v1/chat/completions"
    assert lines[0]["body"]["model"] == "gpt-4o-mini"


def test_encode_rejects_malformed_entries():
    with pytest.raises(ServiceInvalidRequestError):
        open_ai_batch_encode([{"body": {}}])
    with pytest.raises(ServiceInvalidRequestError):
        open_ai_batch_encode([{"custom_id": "x"}])
    with pytest.raises(ServiceInvalidRequestError):
        open_ai_batch_encode([{"custom_id": "x", "body": "not-a-dict"}])


def test_grouped_by_credential_separates_keys():
    batch = Batch(
        requests=[
            BatchRequest(custom_id="a", endpoint="/v1/chat/completions", payload={}, credential_key="k1"),
            BatchRequest(custom_id="b", endpoint="/v1/chat/completions", payload={}, credential_key="k2"),
            BatchRequest(custom_id="c", endpoint="/v1/chat/completions", payload={}, credential_key="k1"),
        ]
    )
    groups = batch.grouped_by_credential()
    assert set(groups) == {"k1", "k2"}
    assert [r.custom_id for r in groups["k1"].requests] == ["a", "c"]
    assert [r.custom_id for r in groups["k2"].requests] == ["b"]


@pytest.mark.asyncio
async def test_create_batch_groups_only_same_credential():
    service = _service()
    uploaded = MagicMock(id="file-1")
    created = _provider_job(id="batch_1", status="validating")
    service.client.files.create.return_value = uploaded
    service.client.batches.create.return_value = created

    batch = Batch(
        requests=[
            BatchRequest(custom_id="a", endpoint="/v1/chat/completions", payload={}, credential_key="k1"),
            BatchRequest(custom_id="b", endpoint="/v1/chat/completions", payload={}, credential_key="k2"),
        ]
    )
    job = await service.create_batch(batch)

    # Two different credential keys -> two provider submissions, never mixed.
    assert service.client.batches.create.await_count == 2
    assert job.job_id == "batch_1+batch_1"
    assert job.request_ids == ["a", "b"]


@pytest.mark.asyncio
async def test_create_batch_rejects_empty():
    with pytest.raises(ServiceInvalidRequestError):
        await _service().create_batch(Batch())


@pytest.mark.asyncio
async def test_create_batch_rejects_duplicate_custom_ids():
    batch = Batch(
        requests=[
            BatchRequest(custom_id="dup", endpoint="/v1/chat/completions", payload={}),
            BatchRequest(custom_id="dup", endpoint="/v1/chat/completions", payload={}, credential_key="other"),
        ]
    )
    with pytest.raises(ServiceInvalidRequestError, match="Duplicate custom_id"):
        await _service().create_batch(batch)


@pytest.mark.asyncio
async def test_create_batch_rejects_mixed_endpoints():
    batch = Batch(
        requests=[
            BatchRequest(custom_id="a", endpoint="/v1/chat/completions", payload={}),
            BatchRequest(custom_id="b", endpoint="/v1/embeddings", payload={}),
        ]
    )
    with pytest.raises(ServiceInvalidRequestError, match="share an endpoint"):
        await _service().create_batch(batch)


@pytest.mark.asyncio
async def test_partial_submit_failure_cancels_earlier_jobs():
    service = _service()
    service.client.files.create.return_value = MagicMock(id="file-1")
    service.client.batches.create.side_effect = [
        _provider_job(id="batch_ok", status="validating"),
        RuntimeError("second group exploded"),
    ]
    batch = Batch(
        requests=[
            BatchRequest(custom_id="a", endpoint="/v1/chat/completions", payload={}, credential_key="k1"),
            BatchRequest(custom_id="b", endpoint="/v1/chat/completions", payload={}, credential_key="k2"),
        ]
    )
    with pytest.raises(ServiceResponseException):
        await service.create_batch(batch)
    service.client.batches.cancel.assert_awaited_once_with("batch_ok")


@pytest.mark.asyncio
async def test_partial_submit_failure_reports_uncancelled_jobs():
    """A failed cleanup cancel must surface retryable ids, not claim success."""
    service = _service()
    service.client.files.create.return_value = MagicMock(id="file-1")
    service.client.batches.create.side_effect = [
        _provider_job(id="batch_stuck", status="validating"),
        RuntimeError("second group exploded"),
    ]
    service.client.batches.cancel.side_effect = RuntimeError("cancel endpoint down")
    batch = Batch(
        requests=[
            BatchRequest(custom_id="a", endpoint="/v1/chat/completions", payload={}, credential_key="k1"),
            BatchRequest(custom_id="b", endpoint="/v1/chat/completions", payload={}, credential_key="k2"),
        ]
    )
    with pytest.raises(ServiceResponseException, match="batch_stuck") as exc_info:
        await service.create_batch(batch)
    # The exception must distinguish "cancel requested" from "cancel failed"
    # and keep the still-running job id so the caller can retry cancel_batch.
    assert "could NOT be cancelled" in str(exc_info.value)
    assert "cancellation requested" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_partial_submit_failure_mixed_cancel_outcome():
    """With several submitted jobs, the exception separates cancelled from stuck ids."""
    service = _service()
    service.client.files.create.return_value = MagicMock(id="file-1")
    service.client.batches.create.side_effect = [
        _provider_job(id="batch_a", status="validating"),
        _provider_job(id="batch_b", status="validating"),
        RuntimeError("third group exploded"),
    ]
    service.client.batches.cancel.side_effect = [MagicMock(id="batch_a"), RuntimeError("boom")]
    batch = Batch(
        requests=[
            BatchRequest(custom_id="a", endpoint="/v1/chat/completions", payload={}, credential_key="k1"),
            BatchRequest(custom_id="b", endpoint="/v1/chat/completions", payload={}, credential_key="k2"),
            BatchRequest(custom_id="c", endpoint="/v1/chat/completions", payload={}, credential_key="k3"),
        ]
    )
    with pytest.raises(ServiceResponseException) as exc_info:
        await service.create_batch(batch)
    message = str(exc_info.value)
    assert "cancellation requested for already-submitted jobs ['batch_a']" in message
    assert "still running" in message and "batch_b" in message


@pytest.mark.asyncio
async def test_status_stays_nonterminal_while_any_child_runs():
    service = _service()
    service.client.batches.retrieve.side_effect = [
        _provider_job(id="b1", status="in_progress", total=3, completed=1, failed=0),
        _provider_job(id="b2", status="failed", total=2, completed=0, failed=2),
    ]
    job = BatchJob(job_id="b1+b2", request_ids=["a", "b"])
    merged = await service.get_batch_status(job)
    # b1 is still running, so the aggregate must not report FAILED (terminal).
    assert merged.status == BatchStatus.IN_PROGRESS
    assert not merged.status.is_terminal
    assert merged.request_counts["total"] == 5
    assert merged.request_counts["failed"] == 2


@pytest.mark.asyncio
async def test_status_terminal_reports_worst():
    service = _service()
    service.client.batches.retrieve.side_effect = [
        _provider_job(id="b1", status="completed", total=3, completed=3, failed=0),
        _provider_job(id="b2", status="failed", total=2, completed=0, failed=2),
    ]
    merged = await service.get_batch_status(BatchJob(job_id="b1+b2"))
    assert merged.status == BatchStatus.FAILED


@pytest.mark.asyncio
async def test_cancel_marks_status():
    service = _service()
    service.client.batches.cancel.return_value = _provider_job(id="b1", status="cancelling")
    job = BatchJob(job_id="b1", request_ids=["a"])
    cancelled = await service.cancel_batch(job)
    assert cancelled.status == BatchStatus.CANCELLING


@pytest.mark.asyncio
async def test_results_rejected_while_jobs_running():
    service = _service()
    service.client.batches.retrieve.return_value = _provider_job(id="b1", status="in_progress")
    with pytest.raises(ServiceInvalidRequestError, match="still running"):
        await service.get_batch_results(BatchJob(job_id="b1", request_ids=["a"]))


@pytest.mark.asyncio
async def test_results_surface_typed_per_request_errors():
    service = _service()
    provider_job = _provider_job(id="b1", status="completed", output_file_id="file-out", error_file_id="file-err")
    service.client.batches.retrieve.return_value = provider_job
    output_lines = "\n".join(
        [
            json.dumps(
                {
                    "custom_id": "ok",
                    "response": {"status_code": 200, "body": {"choices": [{"message": {"content": "done"}}]}},
                }
            ),
            json.dumps(
                {
                    "custom_id": "http_error",
                    "response": {"status_code": 400, "body": {"error": {"message": "bad request"}}},
                }
            ),
        ]
    )
    error_lines = json.dumps({"custom_id": "bad", "error": {"code": "context_length_exceeded", "message": "too long"}})
    service.client.files.content.side_effect = [
        MagicMock(text=output_lines),
        MagicMock(text=error_lines),
    ]

    job = BatchJob(job_id="b1", request_ids=["ok", "bad", "http_error", "unrun"], status=BatchStatus.COMPLETED)
    results = {r.custom_id: r for r in await service.get_batch_results(job)}

    assert results["ok"].succeeded
    assert results["ok"].response["choices"][0]["message"]["content"] == "done"
    # Error file parsed for real error payloads.
    assert not results["bad"].succeeded
    assert "context_length_exceeded" in results["bad"].error
    # A 4xx body is not a usable result even without a top-level error.
    assert not results["http_error"].succeeded
    assert results["http_error"].response is None
    # An unrun/cancelled request must surface a typed result, not be dropped.
    assert not results["unrun"].succeeded
    assert results["unrun"].error is not None


@pytest.mark.asyncio
async def test_expired_requests_reported():
    service = _service()
    provider_job = _provider_job(
        id="b1",
        status="expired",
        output_file_id=None,
        expired_requests={"requests": ["stale"]},
    )
    service.client.batches.retrieve.return_value = provider_job

    job = BatchJob(job_id="b1", request_ids=["stale"], status=BatchStatus.EXPIRED)
    results = await service.get_batch_results(job)
    assert len(results) == 1
    assert results[0].error == "request expired before it ran"


@pytest.mark.asyncio
async def test_result_download_failure_wrapped():
    service = _service()
    service.client.batches.retrieve.return_value = _provider_job(id="b1", status="completed", output_file_id="f1")
    service.client.files.content.side_effect = RuntimeError("download boom")
    with pytest.raises(ServiceResponseException):
        await service.get_batch_results(BatchJob(job_id="b1", request_ids=["a"], status=BatchStatus.COMPLETED))


@pytest.mark.asyncio
async def test_status_failure_raises_service_exception():
    service = _service()
    service.client.batches.retrieve.side_effect = RuntimeError("boom")
    with pytest.raises(ServiceResponseException):
        await service.get_batch_status(BatchJob(job_id="b1"))
