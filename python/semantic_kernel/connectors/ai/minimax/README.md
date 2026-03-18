# semantic_kernel.connectors.ai.minimax

This connector enables integration with MiniMax API for chat completion. It allows you to use MiniMax's models within the Semantic Kernel framework.

MiniMax provides an OpenAI-compatible API, making integration straightforward.

## Quick start

### Initialize the kernel
```python
import semantic_kernel as sk
kernel = sk.Kernel()
```

### Add MiniMax chat completion service
You can provide your API key directly or through environment variables.
```python
from semantic_kernel.connectors.ai.minimax import MiniMaxChatCompletion

chat_service = MiniMaxChatCompletion(
    ai_model_id="MiniMax-M2.7",  # Default model if not specified
    api_key="your-minimax-api-key",  # Can also use MINIMAX_API_KEY env variable
    service_id="minimax-chat"  # Optional service identifier
)
kernel.add_service(chat_service)
```

### Basic chat completion
```python
response = await kernel.invoke_prompt("Hello, how are you?")
```

### Using with Chat Completion Agent
```python
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.minimax import MiniMaxChatCompletion

agent = ChatCompletionAgent(
    service=MiniMaxChatCompletion(),
    name="SK-Assistant",
    instructions="You are a helpful assistant.",
)
response = await agent.get_response(messages="Write a haiku about Semantic Kernel.")
print(response.content)
```

## Available Models

- `MiniMax-M2.7` - Latest flagship model with enhanced reasoning and coding (default)
- `MiniMax-M2.7-highspeed` - High-speed version of M2.7 for low-latency scenarios
- `MiniMax-M2.5` - Standard model with 204K context window
- `MiniMax-M2.5-highspeed` - High-speed variant with 204K context window

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MINIMAX_API_KEY` | Your MiniMax API key |
| `MINIMAX_BASE_URL` | API endpoint (defaults to `https://api.minimax.io/v1`) |
| `MINIMAX_CHAT_MODEL_ID` | Default chat model ID |

## Notes

- MiniMax API accepts temperature in the range [0.0, 1.0].
