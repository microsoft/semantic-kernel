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
[step01_chat_completion_agent_simple](../getting_started_with_agents/chat_completion/step01_chat_completion_agent_simple.py)|How to create and use a simple chat completion agent.
[step02_chat_completion_agent_thread_management](../getting_started_with_agents/chat_completion/step02_chat_completion_agent_thread_management.py)|How to create and use a chat completion with a thread.
[step03_chat_completion_agent_with_kernel](../getting_started_with_agents/chat_completion/step03_chat_completion_agent_with_kernel.py)|How to create and use a a chat completion agent with the AI service created on the kernel.
[step04_chat_completion_agent_plugin_simple](../getting_started_with_agents/chat_completion/step04_chat_completion_agent_plugin_simple.py)|How to create a simple chat completion agent and specify plugins via the constructor with a kernel.
[step05_chat_completion_agent_plugin_with_kernel](../getting_started_with_agents/chat_completion/step05_chat_completion_agent_plugin_with_kernel.py)|How to create and use a chat completion agent by registering plugins on the kernel.
[step06_chat_completion_agent_group_chat](../getting_started_with_agents/chat_completion/step06_chat_completion_agent_group_chat.py)|How to create a conversation between agents.
[step07_kernel_function_strategies](../getting_started_with_agents/chat_completion/step07_kernel_function_strategies.py)|How to utilize a `KernelFunction` as a chat strategy.
[step08_chat_completion_agent_json_result](../getting_started_with_agents/chat_completion/step08_chat_completion_agent_json_result.py)|How to have an agent produce JSON.
[step09_chat_completion_agent_logging](../getting_started_with_agents/chat_completion/step09_chat_completion_agent_logging.py)|How to enable logging for agents.
[step10_chat_completion_agent_structured_outputs](../getting_started_with_agents/chat_completion/step10_chat_completion_agent_structured_outputs.py)|How to use have a chat completion agent use structured outputs
[step11_chat_completion_agent_declarative](../getting_started_with_agents/chat_completion/step11_chat_completion_agent_declarative.py)|How to create a chat compltion agent from a declarative spec.

## Azure AI Agent

Example|Description
---|---
[step1_azure_ai_agent](../getting_started_with_agents/azure_ai_agent/step01_azure_ai_agent.py)|How to create an Azure AI Agent and invoke a Semantic Kernel plugin.
[step2_azure_ai_agent_plugin](../getting_started_with_agents/azure_ai_agent/step02_azure_ai_agent_plugin.py)|How to create an Azure AI Agent with plugins.
[step3_azure_ai_agent_group_chat](../getting_started_with_agents/azure_ai_agent/step03_azure_ai_agent_group_chat.py)|How to create an agent group chat with Azure AI Agents.
[step4_azure_ai_agent_code_interpreter](../getting_started_with_agents/azure_ai_agent/step04_azure_ai_agent_code_interpreter.py)|How to use the code-interpreter tool for an Azure AI agent.
[step5_azure_ai_agent_file_search](../getting_started_with_agents/azure_ai_agent/step05_azure_ai_agent_file_search.py)|How to use the file-search tool for an Azure AI agent.
[step6_azure_ai_agent_openapi](../getting_started_with_agents/azure_ai_agent/step06_azure_ai_agent_openapi.py)|How to use the Open API tool for an Azure AI agent.
[step7_azure_ai_agent_retrieval](../getting_started_with_agents/azure_ai_agent/step07_azure_ai_agent_retrieval.py)|How to reference an existing Azure AI Agent.
[step8_azure_ai_agent_declarative](../getting_started_with_agents/azure_ai_agent/step08_azure_ai_agent_declarative.py)|How to create an Azure AI Agent from a declarative spec.

_Note: For details on configuring an Azure AI Agent, please see [here](../getting_started_with_agents/azure_ai_agent/README.md)._


## OpenAI Assistant Agent

Example|Description
---|---
[step1_assistant](../getting_started_with_agents/openai_assistant/step1_assistant.py)|How to create and use an OpenAI Assistant agent.
[step2_assistant_plugins](../getting_started_with_agents/openai_assistant/step2_assistant_plugins.py)| How to create and use an OpenAI Assistant agent with plugins.
[step3_assistant_vision](../getting_started_with_agents/openai_assistant/step3_assistant_vision.py)|How to provide an image as input to an OpenAI Assistant agent.
[step4_assistant_tool_code_interpreter](../getting_started_with_agents/openai_assistant/step4_assistant_tool_code_interpreter.py)|How to use the code-interpreter tool for an OpenAI Assistant agent.
[step5_assistant_tool_file_search](../getting_started_with_agents/openai_assistant/step5_assistant_tool_file_search.py)|How to use the file-search tool for an OpenAI Assistant agent.
[step6_assistant](../getting_started_with_agents/openai_assistant/step6_assistant_declarative.py)|How to create an Assistant Agent from a declarative spec.

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
[step8_assistant](../getting_started_with_agents/openai_responses/step8_responses_agent_declarative.py)|How to create a Responses Agent from a declarative spec.

## Multi-Agent Orchestration

Example|Description
---|---
[step1_concurrent](../getting_started_with_agents/multi_agent_orchestration/step1_concurrent.py)|How to run agents in parallel on the same task.
[step1a_concurrent_structure_output](../getting_started_with_agents/multi_agent_orchestration/step1a_concurrent_structure_output.py)|How to run agents in parallel on the same task and return structured output.
[step2_sequential](../getting_started_with_agents/multi_agent_orchestration/step2_sequential.py)|How to run agents in sequence to complete a task.
[step2a_sequential_cancellation_token](../getting_started_with_agents/multi_agent_orchestration/step2a_sequential_cancellation_token.py)|How to cancel an invocation while it is in progress.
[step3_group_chat](../getting_started_with_agents/multi_agent_orchestration/step3_group_chat.py)|How to run agents in a group chat to complete a task.
[step3a_group_chat_human_in_the_loop](../getting_started_with_agents/multi_agent_orchestration/step3a_group_chat_human_in_the_loop.py)|How to run agents in a group chat with human in the loop.
[step3b_group_chat_with_chat_completion_manager](../getting_started_with_agents/multi_agent_orchestration/step3b_group_chat_with_chat_completion_manager.py)|How to run agents in a group chat with a more dynamic manager.
[step4_handoff](../getting_started_with_agents/multi_agent_orchestration/step4_handoff.py)|How to run agents in a handoff orchestration to complete a task.
[step4a_handoff_structure_input](../getting_started_with_agents/multi_agent_orchestration/step4a_handoff_structure_input.py)|How to run agents in a handoff orchestration to complete a task with structured input.
[step5_magentic](../getting_started_with_agents/multi_agent_orchestration/step5_magentic.py)|How to run agents in a Magentic orchestration to complete a task.

## Configuring the Kernel

Similar to the Semantic Kernel Python concept samples, it is necessary to configure the secrets
and keys used by the kernel. See the follow "Configuring the Kernel" [guide](../concepts/README.md#configuring-the-kernel) for
more information.

## Running Concept Samples

Concept samples can be run in an IDE or via the command line. After setting up the required api key
for your AI connector, the samples run without any extra command line arguments.
