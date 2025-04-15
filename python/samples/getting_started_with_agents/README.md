# Semantic Kernel Agents - Getting Started

This project contains a step by step guide to get started with _Semantic Kernel Agents_ in Python.

#### PyPI:

- For the use of Chat Completion agents, the minimum allowed Semantic Kernel pypi version is 1.3.0.
- For the use of OpenAI Assistant agents, the minimum allowed Semantic Kernel pypi version is 1.4.0.
- For the use of Agent Group Chat, the minimum allowed Semantic kernel pypi version is 1.6.0.
- For the use of Streaming OpenAI Assistant agents, the minimum allowed Semantic Kernel pypi version is 1.11.0
- For the use of OpenAI Responses agents, the minimum allowed Semantic Kernel pypi version is 1.27.0.

#### Source

- [Semantic Kernel Agent Framework](../../semantic_kernel/agents/)

## Examples

The getting started with agents examples include:

## Chat Completion

Example|Description
---|---
[step1_chat_completion_agent_simple](../getting_started_with_agents/chat_completion/step1_chat_completion_agent_simple.py)|How to create and use a simple chat completion agent.
[step2_chat_completion_agent_thread_management](../getting_started_with_agents/chat_completion/step2_chat_completion_agent_thread_management.py)|How to create and use a chat completion with a thread.
[step3_chat_completion_agent_with_kernel](../getting_started_with_agents/chat_completion/step3_chat_completion_agent_with_kernel.py)|How to create and use a a chat completion agent with the AI service created on the kernel.
[step4_chat_completion_agent_plugin_simple](../getting_started_with_agents/chat_completion/step4_chat_completion_agent_plugin_simple.py)|How to create a simple chat completion agent and specify plugins via the constructor with a kernel.
[step5_chat_completion_agent_plugin_with_kernel](../getting_started_with_agents/chat_completion/step5_chat_completion_agent_plugin_with_kernel.py)|How to create and use a chat completion agent by registering plugins on the kernel.
[step6_chat_completion_agent_group_chat](../getting_started_with_agents/chat_completion/step6_chat_completion_agent_group_chat.py)|How to create a conversation between agents.
[step7_kernel_function_strategies](../getting_started_with_agents/chat_completion/step7_kernel_function_strategies.py)|How to utilize a `KernelFunction` as a chat strategy.
[step8_chat_completion_agent_json_result](../getting_started_with_agents/chat_completion/step8_chat_completion_agent_json_result.py)|How to have an agent produce JSON.
[step9_chat_completion_agent_logging](../getting_started_with_agents/chat_completion/step9_chat_completion_agent_logging.py)|How to enable logging for agents.
[step10_chat_completion_agent_structured_outputs](../getting_started_with_agents/chat_completion/step10_chat_completion_agent_structured_outputs.py)|How to use have a chat completion agent use structured outputs

## Azure AI Agent

Example|Description
---|---
[step1_azure_ai_agent](../getting_started_with_agents/azure_ai_agent/step1_azure_ai_agent.py)|How to create an Azure AI Agent and invoke a Semantic Kernel plugin.
[step2_azure_ai_agent_plugin](../getting_started_with_agents/azure_ai_agent/step2_azure_ai_agent_plugin.py)|How to create an Azure AI Agent with plugins.
[step3_azure_ai_agent_group_chat](../getting_started_with_agents/azure_ai_agent/step3_azure_ai_agent_group_chat.py)|How to create an agent group chat with Azure AI Agents.
[step4_azure_ai_agent_code_interpreter](../getting_started_with_agents/azure_ai_agent/step4_azure_ai_agent_code_interpreter.py)|How to use the code-interpreter tool for an Azure AI agent.
[step5_azure_ai_agent_file_search](../getting_started_with_agents/azure_ai_agent/step5_azure_ai_agent_file_search.py)|How to use the file-search tool for an Azure AI agent.
[step6_azure_ai_agent_openapi](../getting_started_with_agents/azure_ai_agent/step6_azure_ai_agent_openapi.py)|How to use the Open API tool for an Azure AI  agent.

_Note: For details on configuring an Azure AI Agent, please see [here](../getting_started_with_agents/azure_ai_agent/README.md)._

## OpenAI Assistant Agent

Example|Description
---|---
[step1_assistant](../getting_started_with_agents/openai_assistant/step1_assistant.py)|How to create and use an OpenAI Assistant agent.
[step2_assistant_plugins](../getting_started_with_agents/openai_assistant/step2_assistant_plugins.py)| How to create and use an OpenAI Assistant agent with plugins.
[step3_assistant_vision](../getting_started_with_agents/openai_assistant/step3_assistant_vision.py)|How to provide an image as input to an OpenAI Assistant agent.
[step4_assistant_tool_code_interpreter](../getting_started_with_agents/openai_assistant/step4_assistant_tool_code_interpreter.py)|How to use the code-interpreter tool for an OpenAI Assistant agent.
[step5_assistant_tool_file_search](../getting_started_with_agents/openai_assistant/step5_assistant_tool_file_search.py)|How to use the file-search tool for an OpenAI Assistant agent.

## OpenAI Responses Agent

Example|Description
---|---
[step1_responses_agent](../getting_started_with_agents/openai_responses/step1_responses_agent.py)|How to create and use an OpenAI Responses agent in the most simple way.
[step2_responses_agent_thread_management](../getting_started_with_agents/openai_responses/step2_responses_agent_thread_management.py)| How to create and use a `ResponsesAgentThread` agent to maintain conversation context.
[step3_responses_agent_plugins](../getting_started_with_agents/openai_responses/step3_responses_agent_plugins.py)|How to create and use an OpenAI Responses agent with plugins.
[step4_responses_agent_web_search](../getting_started_with_agents/openai_responses/step4_responses_agent_web_search.py)|How to use the web search preview tool with an OpenAI Responses agent.
[step5_responses_agent_file_search](../getting_started_with_agents/openai_responses/step5_responses_agent_file_search.py)|How to use the file-search tool with an OpenAI Responses agent.
[step6_responses_agent_vision](../getting_started_with_agents/openai_responses/step6_responses_agent_vision.py)|How to provide an image as input to an OpenAI Responses agent.
[step7_responses_agent_structured_outputs](../getting_started_with_agents/openai_responses/step7_responses_agent_structured_outputs.py)|How to use have an OpenAI Responses agent use structured outputs.

## Configuring the Kernel

Similar to the Semantic Kernel Python concept samples, it is necessary to configure the secrets
and keys used by the kernel. See the follow "Configuring the Kernel" [guide](../concepts/README.md#configuring-the-kernel) for
more information.

## Running Concept Samples

Concept samples can be run in an IDE or via the command line. After setting up the required api key
for your AI connector, the samples run without any extra command line arguments.
