# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai import (
    AIRequestSettings,
)


def test_default_complete_request_settings():
    settings = AIRequestSettings()
    assert settings.service_id is None
    assert settings.extension_data == {}


def test_custom_complete_request_settings():
    ext_data = {"test": "test"}
    settings = AIRequestSettings(service_id="test", extension_data=ext_data)
    assert settings.service_id == "test"
    assert settings.extension_data["test"] == "test"
