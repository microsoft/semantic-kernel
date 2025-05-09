# Copyright (c) Microsoft. All rights reserved.

import json
from pathlib import Path

from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import (
    KernelProcessStateMetadata,
    KernelProcessStepStateMetadata,
)


def test_load_from_file_success(tmp_path: Path):
    state_data = {"$type": "Process", "id": "123", "name": "TestProcess", "versionInfo": "v1", "stepsState": {}}
    file_path = tmp_path / "test_state.json"
    file_path.write_text(json.dumps(state_data), encoding="utf-8")

    result = KernelProcessStateMetadata.load_from_file(
        json_filename="test_state.json",
        directory=tmp_path,
    )

    assert result is not None
    assert result.id == "123"
    assert result.name == "TestProcess"
    assert result.version_info == "v1"
    assert result.steps_state == {}


def test_load_from_file_file_not_found(tmp_path: Path):
    result = KernelProcessStateMetadata.load_from_file(
        json_filename="non_existing.json",
        directory=tmp_path,
    )
    assert result is None


def test_load_from_file_invalid_json(tmp_path: Path):
    file_path = tmp_path / "invalid.json"
    file_path.write_text("not a valid json content", encoding="utf-8")

    result = KernelProcessStateMetadata.load_from_file(
        json_filename="invalid.json",
        directory=tmp_path,
    )
    assert result is None


async def test_load_from_file_with_non_utf8_encoding(tmp_path: Path):
    state_data = {
        "$type": "Process",
        "id": "456",
        "name": "CaféProcess",
        "versionInfo": "v2",
        "stepsState": {},
    }
    file_path = tmp_path / "test_state_utf16.json"
    file_path.write_text(json.dumps(state_data), encoding="utf-16")

    # Try to read with wrong encoding (utf-8), we expect a parse error -> None
    result_wrong_encoding = KernelProcessStateMetadata.load_from_file(
        json_filename="test_state_utf16.json",
        directory=tmp_path,
        encoding="utf-8",
    )
    assert result_wrong_encoding is None

    # Now read with correct encoding (utf-16), we expect a success
    result_correct_encoding = KernelProcessStateMetadata.load_from_file(
        json_filename="test_state_utf16.json",
        directory=tmp_path,
        encoding="utf-16",
    )
    assert result_correct_encoding is not None
    assert result_correct_encoding.name == "CaféProcess"


def test_create_step_state_metadata():
    step_state = KernelProcessStepStateMetadata(
        type_="Step", id="step123", name="TestStep", version_info="v1", state={"foo": "bar"}
    )

    assert step_state.type_ == "Step"
    assert step_state.id == "step123"
    assert step_state.name == "TestStep"
    assert step_state.version_info == "v1"
    assert step_state.state == {"foo": "bar"}
