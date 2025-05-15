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

## Samples

| Sample                                                                      | Description  |
|-----------------------------------------------------------------------------|--------------|
| [step1_concurrent](step1_concurrent.py)                                  | Run agents in parallel on the same task.  |
| [step1a_concurrent_structure_output](step1a_concurrent_structure_output.py) | Run agents in parallel on the same task and return structured output.  |
| [step2_sequential](step2_sequential.py)                                  | Run agents in sequence to complete a task.  |
| [step2a_sequential_cancellation_token](step2a_sequential_cancellation_token.py) | Cancel an invocation while it is in progress.  |
| [step3_group_chat](step3_group_chat.py)                                  | Run agents in a group chat to complete a task.  |
| [step3a_group_chat_human_in_the_loop](step3a_group_chat_human_in_the_loop.py) | Run agents in a group chat with human in the loop.  |
| [step3b_group_chat_with_chat_completion_manager](step3b_group_chat_with_chat_completion_manager.py) | Run agents in a group chat with a more dynamic manager.  |
| [step4_handoff](step4_handoff.py)                                        | Run agents in a handoff orchestration to complete a task.  |
| [step4a_handoff_structure_input](step4a_handoff_structure_input.py)      | Run agents in a handoff orchestration to complete a task with structured input.  |
| [step5_magentic](step5_magentic.py)                              | Run agents in a Magentic orchestration to complete a task.  |
