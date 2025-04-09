# Copilot Studio Agents interaction

This is a simple example of how to interact with Copilot Studio Agents as they were first-party agents in Semantic Kernel.

![alt text](image.png)

## Rationale

Semantic Kernel already features many different types of agents, including `ChatCompletionAgent`, `AzureAIAgent`, `OpenAIAssistantAgent` or `AutoGenConversableAgent`. All of them though involve code-based agents.

Instead, [Microsoft Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/fundamentals-what-is-copilot-studio) allows you to create declarative, low-code, and easy-to-maintain agents and publish them over multiple channels.

This way, you can create any amount of agents in Copilot Studio and interact with them along with code-based agents in Semantic Kernel, thus being able to use the best of both worlds.

## Implementation

The implementation enables seamless integration with Copilot Studio agents via the DirectLine API. Several key components work together to provide this functionality:

- [`DirectLineClient`](src/copilot_studio/directline_client.py): A utility module that handles all Direct Line API operations including authentication, conversation management, posting user activities, and retrieving bot responses using watermark-based polling.

- [`CopilotAgent`](src/copilot_studio/copilot_agent.py): Implements `CopilotAgent`, which orchestrates interactions with a Copilot Studio bot. It serializes user messages, handles asynchronous polling for responses, and converts bot activities into structured message content.

- [`CopilotAgentThread`](src/copilot_studio/copilot_agent_thread.py): Provides a specialized thread implementation for Copilot Studio conversations, managing Direct Line-specific context such as conversation ID and watermark.

- [`CopilotAgentChannel`](src/copilot_studio/copilot_agent_channel.py): Adds `CopilotStudioAgentChannel`, allowing Copilot Studio agents to participate in multi-agent group chats via the channel-based invocation system.

- [`CopilotMessageContent`](src/copilot_studio/copilot_message_content.py): Introduces `CopilotMessageContent`, an extension of `ChatMessageContent` that can represent rich message types from Copilot Studio—including plain text, adaptive cards, and suggested actions.

Additionally, we do enforce [authentication to the DirectLine API](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configure-web-security).

## Usage

> [!NOTE]
> Working with Copilot Studio Agents requires a [subscription](https://learn.microsoft.com/en-us/microsoft-copilot-studio/requirements-licensing-subscriptions) to Microsoft Copilot Studio.

> [!TIP]
> In this case, we suggest to start with a simple Q&A Agent and supply a PDF to answer some questions. You can find a free sample like [Microsoft Surface Pro 4 User Guide](https://download.microsoft.com/download/2/9/B/29B20383-302C-4517-A006-B0186F04BE28/surface-pro-4-user-guide-EN.pdf)

1. [Create a new agent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/fundamentals-get-started?tabs=web) in Copilot Studio
2. [Publish the agent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-fundamentals-publish-channels?tabs=web)
3. Turn off default authentication under the agent Settings > Security
4. [Setup web channel security](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configure-web-security) and copy the secret value

Once you're done with the above steps, you can use the following code to interact with the Copilot Studio Agent:

1. Copy the `.env.sample` file to `.env` and set the `BOT_SECRET` environment variable to the secret value
2. Run the following code:

```bash
python -m venv .venv

# On Mac/Linux
source .venv/bin/activate
# On Windows
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

chainlit run --port 8081 .\chat.py
```
