# semantic_kernel.connectors.ai.astraflow

This connector enables integration with **Astraflow** (by UCloud / 优刻得), an OpenAI-compatible AI model aggregation platform that supports 200+ models.

Sign up at https://astraflow.ucloud.cn/

## Endpoints

| Region | Base URL | Env var |
|--------|----------|---------|
| Global (US/CA) | `https://api-us-ca.umodelverse.ai/v1` | `ASTRAFLOW_API_KEY` |
| China | `https://api.modelverse.cn/v1` | `ASTRAFLOW_CN_API_KEY` |

## Quick start

### Initialize the kernel
```python
import semantic_kernel as sk
kernel = sk.Kernel()
```

### Add Astraflow text embedding service
```python
from semantic_kernel.connectors.ai.astraflow import AstraflowTextEmbedding

embedding_service = AstraflowTextEmbedding(
    ai_model_id="BAAI/bge-m3",          # model ID on the platform
    api_key="your-astraflow-api-key",   # or set ASTRAFLOW_API_KEY env var
    service_id="astraflow-embeddings",  # optional
)
kernel.add_service(embedding_service)
```

### Generate embeddings
```python
texts = ["Hello, world!", "Semantic Kernel is awesome"]
embeddings = await kernel.get_service("astraflow-embeddings").generate_embeddings(texts)
```

### Add Astraflow chat completion service
```python
from semantic_kernel.connectors.ai.astraflow import AstraflowChatCompletion

chat_service = AstraflowChatCompletion(
    ai_model_id="deepseek-ai/DeepSeek-V3",  # any model on the platform
    api_key="your-astraflow-api-key",        # or set ASTRAFLOW_API_KEY env var
    service_id="astraflow-chat",             # optional
)
kernel.add_service(chat_service)
```

### Basic chat completion
```python
response = await kernel.invoke_prompt("Hello, how are you?")
```

### China endpoint
```python
chat_cn = AstraflowChatCompletion(
    ai_model_id="deepseek-ai/DeepSeek-V3",
    base_url="https://api.modelverse.cn/v1",
    api_key="your-astraflow-cn-api-key",  # or set ASTRAFLOW_CN_API_KEY env var
)
```

### Using with Chat Completion Agent
```python
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.astraflow import AstraflowChatCompletion

agent = ChatCompletionAgent(
    service=AstraflowChatCompletion(),
    name="SK-Assistant",
    instructions="You are a helpful assistant.",
)
response = await agent.get_response(messages="Write a haiku about Semantic Kernel.")
print(response.content)
```
