# Semantic Kernel: Agent concept examples

This project contains a step by step guide to get started with _Semantic Kernel Agents_ in Python.

## PyPI:

- For the use of Chat Completion agents, the minimum allowed Semantic Kernel pypi version is 1.3.0.
- For the use of OpenAI Assistant agents, the minimum allowed Semantic Kernel pypi version is 1.4.0.
- For the use of Agent Group Chat, the minimum allowed Semantic kernel pypi version is 1.6.0.
- For the use of Streaming OpenAI Assistant agents, the minimum allowed Semantic Kernel pypi version is 1.11.0.
- For the use of AzureAI and Bedrock agents, the minimum allowed Semantic Kernel pypi version is 1.21.0.
- For the use of Crew.AI as a plugin, the minimum allowed Semantic Kernel pypi version is 1.21.1.


## Source

- [Semantic Kernel Agent Framework](../../../semantic_kernel/agents/)

## Examples

The concept agents examples are grouped by prefix:

Prefix|Description
---|---
assistant|How to use agents based on the [Open AI Assistant API](https://platform.openai.com/docs/assistants).
autogen_conversable_agent| How to use [AutoGen 0.2 Conversable Agents](https://microsoft.github.io/autogen/0.2/docs/Getting-Started) within Semantic Kernel.
azure_ai_agent|How to use an [Azure AI Agent](https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart?pivots=programming-language-python-azure) within Semantic Kernel.
chat_completion_agent|How to use Semantic Kernel Chat Completion agents that leverage AI Connector Chat Completion APIs.
bedrock|How to use [AWS Bedrock agents](https://aws.amazon.com/bedrock/agents/) in Semantic Kernel.
mixed_chat|How to combine different agent types.
openai_assistant|How to use [OpenAI Assistants](https://platform.openai.com/docs/assistants/overview) in Semantic Kernel.

## Configuring the Kernel

Similar to the Semantic Kernel Python concept samples, it is necessary to configure the secrets
and keys used by the kernel. See the follow "Configuring the Kernel" [guide](../README.md#configuring-the-kernel) for
more information.

## Running Concept Samples

Concept samples can be run in an IDE or via the command line. After setting up the required api key or token authentication
for your AI connector, the samples run without any extra command line arguments.
