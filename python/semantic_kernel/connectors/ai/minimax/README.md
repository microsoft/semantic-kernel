# semantic_kernel.connectors.ai.minimax

This connector enables integration with the MiniMax API for chat completion. MiniMax provides an
OpenAI-compatible chat completion endpoint, so this connector reuses the OpenAI Python client.

## Regional endpoints

MiniMax exposes two regional OpenAI-compatible endpoints. Select the region through
`MiniMaxSettings` (or the `MINIMAX_REGION` environment variable); the base URL is resolved
automatically when `base_url` is not set explicitly.

| Region      | OpenAI-compatible endpoint        |
|-------------|-----------------------------------|
| `global_en` | `https://api.minimax.io/v1`       |
| `cn_zh`     | `https://api.minimaxi.com/v1`     |

## Available models

- `MiniMax-M3` - Latest flagship model with a 1,000,000 token context window and text/image/video
  input support (default).
- `MiniMax-M2.7` - Previous generation flagship model with a 204,800 token context window.

## Quick start

### Initialize the kernel
```python
import semantic_kernel as sk
kernel = sk.Kernel()
```

### Add the MiniMax chat completion service
Provide your API key directly or through environment variables.
```python
from semantic_kernel.connectors.ai.minimax import MiniMaxChatCompletion

chat_service = MiniMaxChatCompletion(
    ai_model_id="MiniMax-M3",          # Defaults to MiniMax-M3
    api_key="...",                     # Can also use MINIMAX_API_KEY env variable
    service_id="minimax-chat",
)
kernel.add_service(chat_service)
```

### Target the China region
```python
from semantic_kernel.connectors.ai.minimax import MiniMaxChatCompletion

chat_service = MiniMaxChatCompletion(ai_model_id="MiniMax-M3", region="cn_zh")
```

### Basic chat completion
```python
response = await kernel.invoke_prompt("Hello, how are you?")
```

## Environment variables

| Variable               | Description                                                              |
|------------------------|--------------------------------------------------------------------------|
| `MINIMAX_API_KEY`      | Your MiniMax API key                                                     |
| `MINIMAX_REGION`       | `global_en` (default) or `cn_zh`                                         |
| `MINIMAX_BASE_URL`     | API endpoint; resolved from the region when not provided                 |
| `MINIMAX_CHAT_MODEL_ID`| Default chat model ID                                                    |

## Notes

- The MiniMax API accepts `temperature` in the range `[0.0, 1.0]`.
