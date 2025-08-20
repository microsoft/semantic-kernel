# Multi-agent orchestration

The Semantic Kernel Agent Framework now supports orchestrating multiple agents to work together to complete a task.

## Background

The following samples are beneficial if you are just getting started with Semantic Kernel.

- [Chat Completion](../../concepts/chat_completion/)
- [Auto Function Calling](../../concepts/auto_function_calling/)
- [Structured Output](../../concepts/structured_output/)
- [Getting Started with Agents](../../getting_started_with_agents/)
- [More advanced agent samples](../../concepts/agents/)

## Prerequisites

The following environment variables are required to run the samples:

- OPENAI_API_KEY
- OPENAI_CHAT_MODEL_ID

However, if you are using other model services, feel free to switch to those in the samples.
Refer to [here](../../concepts/setup/README.md) on how to set up the environment variables for your model service.

## Orchestrations

| **Orchestrations** | **Description**                                                                                                                                                                                     |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Concurrent**     | Useful for tasks that will benefit from independent analysis from multiple agents.                                                                                                                  |
| **Sequential**     | Useful for tasks that require a well-defined step-by-step approach.                                                                                                                                 |
| **Handoff**        | Useful for tasks that are dynamic in nature and don't have a well-defined step-by-step approach.                                                                                                    |
| **GroupChat**      | Useful for tasks that will benefit from inputs from multiple agents and a highly configurable conversation flow.                                                                                    |
| **Magentic**   | GroupChat like with a planner based manager. Inspired by [Magentic One](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/). |

## Limitations

### Agents

Not all agents are supported in all orchestrations. The following table lists the NOT supported Agents for each orchestration and the reason why.

| **Orchestration** | **Not Supported Agents** | **Reason** |
|-------------------|---------------------------|------------|
| Sequential | BedrockAgent | Only user messages are supported for invoking a Bedrock agent. Bedrock Agent is only compatible with the Sequential orchestration when it is the first agent in the sequence. |
| GroupChat | BedrockAgent | Only user messages are supported for invoking a Bedrock agent. The group chat orchestration requires an agent to be able to respond to messages from other agents. |
| Handoff | BedrockAgent | Only user messages are supported for invoking a Bedrock agent. The handoff orchestration requires an agent to be able to respond to messages from other agents. |
| Handoff | CopilotStudioAgent | Copilot Studio Agent does not support local tools, which is required by the handoff orchestration. |
| Magentic | BedrockAgent | Only user messages are supported for invoking a Bedrock agent. The Magentic orchestration requires an agent to be able to respond to messages from other agents. |
