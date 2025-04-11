# Chat Completion Agents

The following samples demonstrate how to get started with Chat Completion Agents using Semantic Kernel.

## Configuring a Chat Completion Agent

The `ChatCompletionAgent` relies on an underlying AI service connector. Depending on the AI service you choose, you may need to install additional packages. Refer to the [official SK documentation](https://learn.microsoft.com/en-us/semantic-kernel/concepts/ai-services/chat-completion/?tabs=csharp-AzureOpenAI%2Cpython-AzureOpenAI%2Cjava-AzureOpenAI&pivots=programming-language-python#installing-the-necessary-packages-1) for guidance on which extras are required.

Next, follow this [configuration guide](../../concepts/README.md#configuring-the-kernel) to set up your environment for running the sample code.

If you're developing outside the Semantic Kernel repository, it's recommended to place your `.env` file at the root of your project. When using VSCode, this allows the IDE to automatically load the `.env` file and make the environment variables available to your application.

This setup enables the following code to work without explicitly passing keyword arguments to the AI service constructor:

```python
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

agent = ChatCompletionAgent(
    service=AzureChatCompletion(),  # No explicit kwargs needed due to environment variable configuration
    name="Assistant",
    instructions="Answer questions about the world in one sentence.",
)
```

If you prefer to configure the service manually, you can do the following:

```python
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

agent = ChatCompletionAgent(
    service=AzureChatCompletion(
        api_key="your-api-key",
        endpoint="your-aoai-endpoint",
        deployment_name="your-deployment-name",
        api_version="2025-03-01-preview"  # Replace with your desired API version
    ),
    name="Assistant",
    instructions="Answer questions about the world in one sentence.",
)
```

For more information about the `ChatCompletionAgent` see Semantic Kernel's official documentation [here](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/chat-completion-agent?pivots=programming-language-python).