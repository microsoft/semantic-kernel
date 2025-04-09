# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai import PromptExecutionSettings


def test_init():
    settings = PromptExecutionSettings()
    assert settings.service_id is None
    assert settings.extension_data == {}


def test_init_with_data():
    ext_data = {"test": "test"}
    settings = PromptExecutionSettings(service_id="test", extension_data=ext_data)
    assert settings.service_id == "test"
    assert settings.extension_data["test"] == "test"
