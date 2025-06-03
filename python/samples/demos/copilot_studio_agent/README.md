# Copilot Studio Agents interaction

This is a simple example of how to interact with Copilot Studio Agents as they were first-party agents in Semantic Kernel.

![alt text](image.png)

## Rationale

Semantic Kernel already features many different types of agents, including `ChatCompletionAgent`, `AzureAIAgent`, `OpenAIAssistantAgent` or `AutoGenConversableAgent`. All of them though involve code-based agents.

Instead, [Microsoft Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/fundamentals-what-is-copilot-studio) allows you to create declarative, low-code, and easy-to-maintain agents and publish them over multiple channels.

This way, you can create any amount of agents in Copilot Studio and interact with them along with code-based agents in Semantic Kernel, thus being able to use the best of both worlds.

## Implementation

The implementation enables seamless integration with Copilot Studio agents via the DirectLine API. Several key components work together to provide this functionality:

- [`DirectLineClient`](src/agents/copilot_studio/directline_client.py): A utility module that handles all Direct Line API operations including authentication, conversation management, posting user activities, and retrieving bot responses using watermark-based polling.

- [`CopilotAgent`](src/agents/copilot_studio/copilot_agent.py): Implements `CopilotAgent`, which orchestrates interactions with a Copilot Studio bot. It serializes user messages, handles asynchronous polling for responses, and converts bot activities into structured message content.

- [`CopilotAgentThread`](src/agents/copilot_studio/copilot_agent_thread.py): Provides a specialized thread implementation for Copilot Studio conversations, managing Direct Line-specific context such as conversation ID and watermark.

- [`CopilotAgentChannel`](src/agents/copilot_studio/copilot_agent_channel.py): Adds `CopilotStudioAgentChannel`, allowing Copilot Studio agents to participate in multi-agent group chats via the channel-based invocation system.

- [`CopilotMessageContent`](src/agents/copilot_studio/copilot_message_content.py): Introduces `CopilotMessageContent`, an extension of `ChatMessageContent` that can represent rich message types from Copilot Studio—including plain text, adaptive cards, and suggested actions.

Additionally, we do enforce [authentication to the DirectLine API](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configure-web-security).

## Usage

> [!NOTE]
> Working with Copilot Studio Agents requires a [subscription](https://learn.microsoft.com/en-us/microsoft-copilot-studio/requirements-licensing-subscriptions) to Microsoft Copilot Studio.

For this sample, we have created two agents in Copilot Studio:
- The **TaglineGenerator agent** creates taglines for products based on descriptions
- The **BrandAuditor agent** evaluates and approves/rejects taglines based on brand guidelines

The TaglineGenerator is used in the single agent chat example, allowing you to interact with it directly. In the group chat example, both the TaglineGenerator and the BrandAuditor agents collaborate to create and refine taglines that meet brand requirements.

### Setting Up Copilot Studio Agents
Follow these steps to set up your Copilot Studio agents:

1. [Create a new agent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/fundamentals-get-started?tabs=web) in Copilot Studio
2. [Publish the agent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-fundamentals-publish-channels?tabs=web)
3. Turn off default authentication under the agent Settings > Security
4. [Setup web channel security](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configure-web-security) and copy the secret value

### Setting Up Environment

1. Copy the `.env.sample` file to `.env` and add the agent secrets to your `.env` file:
```
AUDITOR_AGENT_SECRET=your_tagline_agent_secret
BRAND_AGENT_SECRET=your_brand_auditor_agent_secret
```
2. Set up your environment:

```bash
python -m venv .venv

# On Mac/Linux
source .venv/bin/activate
# On Windows
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Running the Single Agent Chat

```bash
chainlit run --port 8081 .\chat.py
```

The chat.py file demonstrates a web-based chat interface that allows for multi-turn conversations with a single agent.

### Running the Agent Group Chat

```bash
python group_chat.py
```

The agents will collaborate automatically, with the TaglineGenerator creating taglines and the BrandAuditor providing feedback until a satisfactory tagline is approved.
