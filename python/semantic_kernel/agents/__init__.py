# Copyright (c) Microsoft. All rights reserved.

import importlib

_AGENTS = {
    "Agent": ".agent",
    "AgentResponseItem": ".agent",
    "AgentThread": ".agent",
    "AutoGenConversableAgent": ".autogen.autogen_conversable_agent",
    "AutoGenConversableAgentThread": ".autogen.autogen_conversable_agent",
    "AzureAIAgent": ".azure_ai.azure_ai_agent",
    "AzureAIAgentSettings": ".azure_ai.azure_ai_agent_settings",
    "AzureAIAgentThread": ".azure_ai.azure_ai_agent",
    "BedrockAgent": ".bedrock.bedrock_agent",
    "BedrockAgentThread": ".bedrock.bedrock_agent",
    "ChatCompletionAgent": ".chat_completion.chat_completion_agent",
    "ChatHistoryAgentThread": ".chat_completion.chat_completion_agent",
    "CopilotStudioAgent": ".copilot_studio.copilot_studio_agent",
    "CopilotStudioAgentAuthMode": ".copilot_studio.copilot_studio_agent_settings",
    "CopilotStudioAgentSettings": ".copilot_studio.copilot_studio_agent_settings",
    "CopilotStudioAgentThread": ".copilot_studio.copilot_studio_agent",
    "AgentChat": ".group_chat.agent_chat",
    "AgentGroupChat": ".group_chat.agent_group_chat",
    "AzureAssistantAgent": ".open_ai.azure_assistant_agent",
    "AssistantAgentThread": ".open_ai.open_ai_assistant_agent",
    "OpenAIAssistantAgent": ".open_ai.open_ai_assistant_agent",
    "OpenAIResponsesAgent": ".open_ai.openai_responses_agent",
    "AzureResponsesAgent": ".open_ai.azure_responses_agent",
    "ResponsesAgentThread": ".open_ai.openai_responses_agent",
    "RunPollingOptions": ".open_ai.run_polling_options",
}


def __getattr__(name: str):
    if name in _AGENTS:
        submod_name = _AGENTS[name]
        module = importlib.import_module(submod_name, package=__name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


def __dir__():
    return list(_AGENTS.keys())
