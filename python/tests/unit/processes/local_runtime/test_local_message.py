# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.processes.local_runtime.local_message import LocalMessage


def test_initialization_with_all_fields():
    # Arrange
    source_id = "source_001"
    destination_id = "destination_001"
    function_name = "process_data"
    values = {"param": "value"}
    target_event_id = "event_001"
    target_event_data = {"key": "value"}

    # Act
    message = LocalMessage(
        source_id=source_id,
        destination_id=destination_id,
        function_name=function_name,
        values=values,
        target_event_id=target_event_id,
        target_event_data=target_event_data,
    )

    # Assert
    assert message.source_id == source_id
    assert message.destination_id == destination_id
    assert message.function_name == function_name
    assert message.values == values
    assert message.target_event_id == target_event_id
    assert message.target_event_data == target_event_data


def test_initialization_with_required_fields_only():
    # Arrange
    source_id = "source_002"
    destination_id = "destination_002"
    function_name = "execute_task"
    values = {"input": "data"}

    # Act
    message = LocalMessage(
        source_id=source_id, destination_id=destination_id, function_name=function_name, values=values
    )

    # Assert
    assert message.source_id == source_id
    assert message.destination_id == destination_id
    assert message.function_name == function_name
    assert message.values == values
    assert message.target_event_id is None
    assert message.target_event_data is None


def test_initialization_with_empty_values():
    # Arrange
    source_id = "source_003"
    destination_id = "destination_003"
    function_name = "no_op"
    values = {}

    # Act
    message = LocalMessage(
        source_id=source_id, destination_id=destination_id, function_name=function_name, values=values
    )

    # Assert
    assert message.source_id == source_id
    assert message.destination_id == destination_id
    assert message.function_name == function_name
    assert message.values == values
    assert message.target_event_id is None
    assert message.target_event_data is None


def test_initialization_invalid_source_id():
    # Arrange
    source_id = None  # Invalid type
    destination_id = "destination_004"
    function_name = "invalid_test"
    values = {"input": "data"}

    # Act & Assert
    with pytest.raises(ValueError):
        LocalMessage(source_id=source_id, destination_id=destination_id, function_name=function_name, values=values)


def test_initialization_invalid_destination_id():
    # Arrange
    source_id = "source_004"
    destination_id = None  # Invalid type
    function_name = "invalid_test"
    values = {"input": "data"}

    # Act & Assert
    with pytest.raises(ValueError):
        LocalMessage(source_id=source_id, destination_id=destination_id, function_name=function_name, values=values)


def test_initialization_invalid_function_name():
    # Arrange
    source_id = "source_005"
    destination_id = "destination_005"
    function_name = None  # Invalid type
    values = {"input": "data"}

    # Act & Assert
    with pytest.raises(ValueError):
        LocalMessage(source_id=source_id, destination_id=destination_id, function_name=function_name, values=values)
