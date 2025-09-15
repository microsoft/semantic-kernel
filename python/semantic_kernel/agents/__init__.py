# Copyright (c) Microsoft. All rights reserved.

import importlib

_AGENTS = {
    "Agent": ".agent",
    "AgentChat": ".group_chat.agent_chat",
    "AgentGroupChat": ".group_chat.agent_group_chat",
    "AgentSpec": ".agent",
    "AgentRegistry": ".agent",
    "AgentResponseItem": ".agent",
    "AgentThread": ".agent",
    "AutoGenConversableAgent": ".autogen.autogen_conversable_agent",
    "AutoGenConversableAgentThread": ".autogen.autogen_conversable_agent",
    "AzureAIAgent": ".azure_ai.azure_ai_agent",
    "AzureAIAgentSettings": ".azure_ai.azure_ai_agent_settings",
    "AzureAIAgentThread": ".azure_ai.azure_ai_agent",
    "AzureAssistantAgent": ".open_ai.azure_assistant_agent",
    "AssistantAgentThread": ".open_ai.openai_assistant_agent",
    "AzureResponsesAgent": ".open_ai.azure_responses_agent",
    "BedrockAgent": ".bedrock.bedrock_agent",
    "BedrockAgentThread": ".bedrock.bedrock_agent",
    "ChatCompletionAgent": ".chat_completion.chat_completion_agent",
    "ChatHistoryAgentThread": ".chat_completion.chat_completion_agent",
    "CopilotStudioAgent": ".copilot_studio.copilot_studio_agent",
    "CopilotStudioAgentAuthMode": ".copilot_studio.copilot_studio_agent_settings",
    "CopilotStudioAgentSettings": ".copilot_studio.copilot_studio_agent_settings",
    "CopilotStudioAgentThread": ".copilot_studio.copilot_studio_agent",
    "DeclarativeSpecMixin": ".agent",
    "OpenAIAssistantAgent": ".open_ai.openai_assistant_agent",
    "OpenAIResponsesAgent": ".open_ai.openai_responses_agent",
    "ModelConnection": ".agent",
    "ModelSpec": ".agent",
    "ResponsesAgentThread": ".open_ai.openai_responses_agent",
    "RunPollingOptions": ".open_ai.run_polling_options",
    "register_agent_type": ".agent",
    "ToolSpec": ".agent",
    "ConcurrentOrchestration": ".orchestration.concurrent",
    "SequentialOrchestration": ".orchestration.sequential",
    "HandoffOrchestration": ".orchestration.handoffs",
    "OrchestrationHandoffs": ".orchestration.handoffs",
    "GroupChatOrchestration": ".orchestration.group_chat",
    "RoundRobinGroupChatManager": ".orchestration.group_chat",
    "BooleanResult": ".orchestration.group_chat",
    "StringResult": ".orchestration.group_chat",
    "MessageResult": ".orchestration.group_chat",
    "GroupChatManager": ".orchestration.group_chat",
    "MagenticOrchestration": ".orchestration.magentic",
    "ProgressLedger": ".orchestration.magentic",
    "MagenticManagerBase": ".orchestration.magentic",
    "StandardMagenticManager": ".orchestration.magentic",
}


def __getattr__(name: str):
    if name in _AGENTS:
        submod_name = _AGENTS[name]
        module = importlib.import_module(submod_name, package=__name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


def __dir__():
    return list(_AGENTS.keys())
