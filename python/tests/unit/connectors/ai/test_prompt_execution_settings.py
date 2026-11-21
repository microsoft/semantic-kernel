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


def test_function_choice_behavior_dict_keeps_auto_invoke_default():
    """A dict function_choice_behavior of type 'auto' must keep auto-invocation enabled.

    It should parse the same way as the string form ("auto"), which yields
    maximum_auto_invoke_attempts == DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS.
    """
    settings = PromptExecutionSettings(function_choice_behavior={"type": "auto"})
    assert settings.function_choice_behavior is not None
    assert settings.function_choice_behavior.type_.value == "auto"
    assert settings.function_choice_behavior.auto_invoke_kernel_functions is True


def test_function_choice_behavior_dict_explicit_auto_invoke_false_is_kept():
    """An explicit `auto_invoke: False` in the dict still disables auto-invocation."""
    settings = PromptExecutionSettings(function_choice_behavior={"type": "auto", "auto_invoke": False})
    assert settings.function_choice_behavior is not None
    assert settings.function_choice_behavior.auto_invoke_kernel_functions is False
