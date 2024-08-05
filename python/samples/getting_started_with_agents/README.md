# Semantic Kernel Agents - Getting Started

This project contains a step by step guide to get started with _Semantic Kernel Agents_ in Python.

#### PyPI:
- For the use of Chat Completion agents, the minimum allowed Semantic Kernel pypi version is 1.3.0.
- For the use of OpenAI Assistant agents, the minimum allowed Semantic Kernel pypi version is 1.4.0.

#### Source

- [Semantic Kernel Agent Framework](../../semantic_kernel/agents/)

## Examples

The getting started with agents examples include:

Example|Description
---|---
[step1_agent](../getting_started_with_agents/step1_agent.py)|How to create and use an agent.
[step2_plugins](../getting_started_with_agents/step2_plugins.py)|How to associate plugins with an agent.
[step8_openai_assistant_agent](../getting_started_with_agents/step8_openai_assistant_agent.py)|How to create and use an OpenAI Assistant agent.

*Note: As we strive for parity with .NET, more getting_started_with_agent samples will be added. The current steps and names may be revised to further align with our .NET counterpart.*

## Configuring the Kernel

Similar to the Semantic Kernel Python concept samples, it is necessary to configure the secrets
and keys used by the kernel. See the follow "Configuring the Kernel" [guide](../concepts/README.md#configuring-the-kernell) for
more information.

## Running Concept Samples

Concept samples can be run in an IDE or via the command line. After setting up the required api key
for your AI connector, the samples run without any extra command line arguments.
