# Copyright (c) Microsoft. All rights reserved.

import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai


def test_plugin_can_be_imported():
    # create a kernel
    kernel = sk.Kernel()
    api_key = "test-api-key"
    org_id = "test-org-id"
    kernel.add_text_completion_service(
        "test-completion-service",
        sk_oai.OpenAITextCompletion("text-davinci-003", api_key, org_id),
    )

    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../..", "test_plugins")
    # path to plugins directory
    plugin_config_dict = kernel.import_semantic_plugin_from_directory(plugins_directory, "TestPlugin")

    assert plugin_config_dict is not None
    assert len(plugin_config_dict) == 1
    assert "TestFunction" in plugin_config_dict
    plugin_config = plugin_config_dict["TestFunction"]
    assert plugin_config.name == "TestFunction"
    assert plugin_config.description == "Test Description"


def test_native_plugin_can_be_imported():
    # create a kernel
    kernel = sk.Kernel()

    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../..", "test_native_plugins")
    # path to plugins directory
    plugin_config_dict = kernel.import_native_plugin_from_directory(plugins_directory, "TestNativePlugin")

    assert plugin_config_dict is not None
    assert len(plugin_config_dict) == 1
    assert "echoAsync" in plugin_config_dict
    plugin_config = plugin_config_dict["echoAsync"]
    assert plugin_config.name == "echoAsync"
    assert plugin_config.description == "Echo for input text"
