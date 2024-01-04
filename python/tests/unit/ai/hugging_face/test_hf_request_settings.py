# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.hugging_face.hf_request_settings import (
    HuggingFaceRequestSettings,
)


@pytest.mark.xfail(reason="GitHub Actions ignores Hugging Face dependencies")
def test_custom_hf_text_request_settings():
    settings = HuggingFaceRequestSettings(
        max_new_tokens=80,
        temperature=0.7,
        top_p=1,
    )

    # Asserting the settings attributes directly
    assert settings.max_new_tokens == 80
    assert settings.temperature == 0.7
    assert settings.top_p == 1

    # Testing prepare_settings_dict
    options = settings.prepare_settings_dict()
    gen_config = options.get("generation_config")

    # Accessing attributes of GenerationConfig object directly
    assert gen_config.max_new_tokens == 80
    assert gen_config.temperature == 0.7
    assert gen_config.top_p == 1
