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

Example|Description
---|---
[step1_agent](../getting_started_with_agents/step1_agent.py)|How to create and use an agent.
[step2_plugins](../getting_started_with_agents/step2_plugins.py)|How to associate plugins with an agent.
[step3_chat](../getting_started_with_agents/step3_chat.py)|How to create a conversation between agents.
[step4_kernel_function_strategies](../getting_started_with_agents/step4_kernel_function_strategies.py)|How to utilize a `KernelFunction` as a chat strategy.
[step5_json_result](../getting_started_with_agents/step5_json_result.py)|How to have an agent produce JSON.
[step6_logging](../getting_started_with_agents/step6_logging.py)|How to enable logging for agents.
[step7_assistant](../getting_started_with_agents/step7_assistant.py)|How to create and use an OpenAI Assistant agent.
[step8_assistant_vision](../getting_started_with_agents/step8_assistant_vision.py)|How to provide an image as input to an Open AI Assistant agent.
[step9_assistant_tool_code_interpreter](../getting_started_with_agents/step9_assistant_tool_code_interpreter.py)|How to use the code-interpreter tool for an Open AI Assistant agent.
[step10_assistant_tool_file_search](../getting_started_with_agents/step10_assistant_tool_file_search.py)|How to use the file-search tool for an Open AI Assistant agent.

*Note: As we strive for parity with .NET, more getting_started_with_agent samples will be added. The current steps and names may be revised to further align with our .NET counterpart.*

## Configuring the Kernel

Similar to the Semantic Kernel Python concept samples, it is necessary to configure the secrets
and keys used by the kernel. See the follow "Configuring the Kernel" [guide](../concepts/README.md#configuring-the-kernel) for
more information.

## Running Concept Samples

Concept samples can be run in an IDE or via the command line. After setting up the required api key
for your AI connector, the samples run without any extra command line arguments.
