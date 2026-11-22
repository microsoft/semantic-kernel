# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings


def test_init():
    settings = PromptExecutionSettings()
    assert settings.service_id is None
    assert settings.extension_data == {}


def test_init_with_data():
    ext_data = {"test": "test"}
    settings = PromptExecutionSettings(service_id="test", extension_data=ext_data)
    assert settings.service_id == "test"
    assert settings.extension_data["test"] == "test"


def test_constructor_override_does_not_change_shared_extension_data():
    extension_data = {"temperature": 0.2}

    override = OpenAIChatPromptExecutionSettings(extension_data=extension_data, temperature=0.8)
    default = OpenAIChatPromptExecutionSettings(extension_data=extension_data)

    assert override.prepare_settings_dict()["temperature"] == 0.8
    assert default.prepare_settings_dict()["temperature"] == 0.2
    assert extension_data == {"temperature": 0.2}
