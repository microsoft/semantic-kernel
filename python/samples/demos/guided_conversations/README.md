# Guided Conversations
This sample highlights a framework for a pattern of use cases we refer to as guided conversations. 
These are scenarios where an agent with a goal and constraints leads a conversation. There are many of these scenarios where we hold conversations that are driven by an objective and constraints. For example:
- a teacher guiding a student through a lesson
- a call center representative collecting information about a customer's issue
- a sales representative helping a customer find the right product for their specific needs
- an interviewer asking candidate a series of questions to assess their fit for a role
- a nurse asking a series of questions to triage the severity of a patient's symptoms
- a meeting where participants go around sharing their updates and discussing next steps

The common thread between all these scenarios is that they are between a **creator** leading the conversation and a **user(s)** who are participating.
The creator defines the goals, a plan for how the conversation should flow, and often collects key information through a form throughout the conversation. 
They must exercise judgment to navigate and adapt the conversation towards achieving the set goal all while writing down key information and planning in advance.

The goal of this framework is to show how we can build a common framework to create AI agents that can assist a creator in running conversational scenarios semi-autonomously and generating **artifacts** like notes, forms, and plans that can be used to track progress and outcomes. A key tenant of this framework is the following principal: *think with the model, plan with the code*. This means that the model is used to understand user inputs and make complex decisions, but code is used to apply constraints and provide structure to make the system **reliable**. To better understand this concept, start with the [notebooks](./notebooks/).


## Features
We were motivated to create this sample while noticing some common challenges with using agents for conversation scenarios:
| Common Challenges                                                                             | Guided Conversations                                                                                                                                                                                                                                                                                                                                             |
| --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Focus - Drift from their original goals                                                       | Define the agent's goal in terms of completing an ["artifact"](./guided_conversation/plugins/artifact.py), which is a precise representation of what the agent needs to do in the conversation                                                                                                                                                                   |
| Pacing - Rushing through conversations, being overly verbose, and struggle to understand time | Encourage the agent to regularly update an [agenda](./guided_conversation/plugins/agenda.py) where each agenda item is allocated an estimated number of times, time limits are programmatically validated, and programmatically convert time-based units (e.g. seconds, minutes) to turns using [resource constraints](./guided_conversation/utils/resources.py) |
| Downstream Use Cases - Difficult to use chat logs for further processing or analysis          | The [artifact](./guided_conversation/plugins/artifact.py) serves as (1) a structured record of the conversation that can be more easily analyzed afterward, (2) a way to monitor the agent's progress in real-time                                                                                                                                               |


## Installation
This sample uses the same tooling as the [Semantic Kernel](https://github.com/microsoft/semantic-kernel/blob/main/python/pyproject.toml) Python source which uses [poetry](https://python-poetry.org/docs/) to install dependencies for development.

1. `poetry install`
1. Activate `.venv` that was created by poetry
1. Set up the environment variables or a `.env` file for the LLM service you want to use.
1. If you add new dependencies to the `pyproject.toml` file; run `poetry update`.


### Quickstart
1. Fork the repository.
1. Install dependencies (see Installation) & set up environment variables
1. Try the [01_guided_conversation_teaching.ipynb](./notebooks/01_guided_conversation_teaching.ipynb) as an example.
1. For best quality and reliability, we recommend using the `gpt-4-1106-preview` or `gpt-4o` models since this sample requires complex reasoning and function calling abilities.


## How You Can Use This Framework 
### Add a new scenario
Create a new file and and define the following inputs:
- An artifact
- Rules 
- Conversation flow (optional)
- Context (optional)
- Resource constraint (optional)

See the [interactive script](./interactive_guided_conversation.py) for an example.

### Editing Existing Plugins
Edit plugins at [plugins](./guided_conversation/plugins/)

### Editing the Orchestrator
Go to [guided_conversation_agent.py](./guided_conversation/plugins/guided_conversation_agent.py). 

### Reusing Plugins
We also encourage the open source community to pull in the artifact and agenda plugins to accelerate existing work. We believe that these plugins alone can improve goal-following in other agents.
