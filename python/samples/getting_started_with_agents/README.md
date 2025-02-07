# Semantic Kernel Agents - Getting Started

This project contains a step by step guide to get started with _Semantic Kernel Agents_ in Python.

#### PyPI:
- For the use of Chat Completion agents, the minimum allowed Semantic Kernel pypi version is 1.3.0.
- For the use of OpenAI Assistant agents, the minimum allowed Semantic Kernel pypi version is 1.4.0.
- For the use of Agent Group Chat, the minimum allowed Semantic kernel pypi version is 1.6.0.
- For the use of Streaming OpenAI Assistant agents, the minimum allowed Semantic Kernel pypi version is 1.11.0

#### Source

- [Semantic Kernel Agent Framework](../../semantic_kernel/agents/)

## Examples

The getting started with agents examples include:

## Chat Completion

Example|Description
---|---
[step1_agent](../getting_started_with_agents/chat_completion/step1_agent.py)|How to create and use an agent.
[step2_plugins](../getting_started_with_agents/chat_completion/step2_plugins.py)|How to associate plugins with an agent.
[step3_chat](../getting_started_with_agents/chat_completion/step3_chat.py)|How to create a conversation between agents.
[step4_kernel_function_strategies](../getting_started_with_agents/chat_completion/step4_kernel_function_strategies.py)|How to utilize a `KernelFunction` as a chat strategy.
[step5_json_result](../getting_started_with_agents/chat_completion/step5_json_result.py)|How to have an agent produce JSON.
[step6_logging](../getting_started_with_agents/chat_completion/step6_logging.py)|How to enable logging for agents.

## OpenAI Assistant

Example|Description
---|---
[step1_assistant](../getting_started_with_agents/openai_assistant/step1_assistant.py)|How to create and use an OpenAI Assistant agent.
[step2_assistant_vision](../getting_started_with_agents/openai_assistant/step2_assistant_vision.py)|How to provide an image as input to an Open AI Assistant agent.
[step3_assistant_tool_code_interpreter](../getting_started_with_agents/openai_assistant/step3_assistant_tool_code_interpreter.py)|How to use the code-interpreter tool for an Open AI Assistant agent.
[step4_assistant_tool_file_search](../getting_started_with_agents/openai_assistant/step4_assistant_tool_file_search.py)|How to use the file-search tool for an Open AI Assistant agent.

## Azure AI Agent
Example|Description
---|---
[step1_azure_ai_agent](../getting_started_with_agents/azure_ai_agent/step1_azure_ai_agent.py)|How to create an Azure AI Agent and invoke a Semantic Kernel plugin.
[step2_azure_ai_agent_chat](../getting_started_with_agents/azure_ai_agent/step2_azure_ai_agent_chat.py)|How to an agent group chat with Azure AI Agents.
[step3_azure_ai_agent_code_interpreter](../getting_started_with_agents/azure_ai_agent/step3_azure_ai_agent_code_interpreter.py)|How to use the code-interpreter tool for an Azure AI agent.
[step4_azure_ai_agent_file_search](../getting_started_with_agents/azure_ai_agent/step4_azure_ai_agent_file_search.py)|How to use the file-search tool for an Azure AI agent.
[step5_azure_ai_agent_openapi](../getting_started_with_agents/azure_ai_agent/step5_azure_ai_agent_openapi.py)|How to use the Open API tool for an Azure AI  agent.

_Note: For details on configuring an Azure AI Agent, please see [here](../getting_started_with_agents/azure_ai_agent/README.md)._

## Configuring the Kernel

Similar to the Semantic Kernel Python concept samples, it is necessary to configure the secrets
and keys used by the kernel. See the follow "Configuring the Kernel" [guide](../concepts/README.md#configuring-the-kernel) for
more information.

## Running Concept Samples

Concept samples can be run in an IDE or via the command line. After setting up the required api key
for your AI connector, the samples run without any extra command line arguments.
