# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.core_plugins.conversation_summary_plugin import ConversationSummaryPlugin
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def test_conversation_summary_plugin():
    config = PromptTemplateConfig(name="test", description="test")
    plugin = ConversationSummaryPlugin(config)
    assert plugin._summarizeConversationFunction is not None
    assert plugin.return_key == "summary"


def test_conversation_summary_plugin_with_deprecated_value(kernel):
    config = PromptTemplateConfig(name="test", description="test")
    plugin = ConversationSummaryPlugin(config, kernel=kernel)
    assert plugin._summarizeConversationFunction is not None
    assert plugin.return_key == "summary"
