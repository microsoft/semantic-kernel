# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.ai.camb.settings.camb_settings import CambSettings


def test_settings_from_env(camb_unit_test_env):
    settings = CambSettings()
    assert settings.api_key.get_secret_value() == camb_unit_test_env["CAMB_API_KEY"]
    assert settings.text_to_audio_model_id == camb_unit_test_env["CAMB_TEXT_TO_AUDIO_MODEL_ID"]


def test_settings_with_explicit_values():
    settings = CambSettings(api_key="my-key", text_to_audio_model_id="mars-pro")
    assert settings.api_key.get_secret_value() == "my-key"
    assert settings.text_to_audio_model_id == "mars-pro"


def test_settings_optional_model_id():
    settings = CambSettings(api_key="my-key")
    assert settings.text_to_audio_model_id is None


@pytest.mark.parametrize("exclude_list", [["CAMB_API_KEY"]], indirect=True)
def test_settings_missing_api_key(camb_unit_test_env):
    with pytest.raises(ValidationError):
        CambSettings()
