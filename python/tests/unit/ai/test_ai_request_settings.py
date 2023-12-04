# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai import (
    AIRequestSettings,
)


def test_default_complete_request_settings():
    settings = AIRequestSettings()
    assert settings.service_id is None
    assert settings.extension_data is None


def test_custom_complete_request_settings():
    ext_data = {"test": "test"}
    settings = AIRequestSettings(service_id="test", extension_data=ext_data)
    assert settings.service_id == "test"
    assert settings.extension_data["test"] == "test"


# def test_default_chat_request_settings():
#     settings = AIRequestSettings()
#     assert settings.temperature == 0.0
#     assert settings.top_p == 1.0
#     assert settings.presence_penalty == 0.0
#     assert settings.frequency_penalty == 0.0
#     assert settings.max_tokens == 256
#     assert settings.stop_sequences == []
#     assert settings.number_of_responses == 1
#     assert settings.token_selection_biases == {}


# def test_complete_request_settings_from_default_completion_config():
#     settings = AIRequestSettings()
#     chat_settings = AIRequestSettings.from_completion_config(settings)
#     chat_settings = AIRequestSettings()
#     assert chat_settings.temperature == 0.0
#     assert chat_settings.top_p == 1.0
#     assert chat_settings.presence_penalty == 0.0
#     assert chat_settings.frequency_penalty == 0.0
#     assert chat_settings.max_tokens == 256
#     assert chat_settings.stop_sequences == []
#     assert chat_settings.number_of_responses == 1
#     assert chat_settings.token_selection_biases == {}


# def test_chat_request_settings_from_custom_completion_config():
#     settings = AIRequestSettings(
#         temperature=0.5,
#         top_p=0.5,
#         presence_penalty=0.5,
#         frequency_penalty=0.5,
#         max_tokens=128,
#         stop_sequences=["\n"],
#         number_of_responses=2,
#         logprobs=1,
#         token_selection_biases={1: 1},
#         chat_system_prompt="Hello",
#     )
#     chat_settings = AIRequestSettings.from_completion_config(settings)
#     assert chat_settings.temperature == 0.5
#     assert chat_settings.top_p == 0.5
#     assert chat_settings.presence_penalty == 0.5
#     assert chat_settings.frequency_penalty == 0.5
#     assert chat_settings.max_tokens == 128
#     assert chat_settings.stop_sequences == ["\n"]
#     assert chat_settings.number_of_responses == 2
#     assert chat_settings.token_selection_biases == {1: 1}
