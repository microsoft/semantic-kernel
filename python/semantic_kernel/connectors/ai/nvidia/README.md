# semantic_kernel.connectors.ai.nvidia

This connector enables integration with NVIDIA NIM API for text embeddings and chat completion. It allows you to use NVIDIA's models within the Semantic Kernel framework.

## Quick start

### Initialize the kernel
```python
import semantic_kernel as sk
kernel = sk.Kernel()
```

### Add NVIDIA text embedding service
You can provide your API key directly or through environment variables
```python
from semantic_kernel.connectors.ai.nvidia import NvidiaTextEmbedding

embedding_service = NvidiaTextEmbedding(
ai_model_id="nvidia/nv-embedqa-e5-v5", # Default model if not specified
api_key="your-nvidia-api-key", # Can also use NVIDIA_API_KEY env variable
service_id="nvidia-embeddings" # Optional service identifier
)
```

### Add the embedding service to the kernel
```python
kernel.add_service(embedding_service)
```

### Generate embeddings for text
```python
texts = ["Hello, world!", "Semantic Kernel is awesome"]
embeddings = await kernel.get_service("nvidia-embeddings").generate_embeddings(texts)
```

### Add NVIDIA chat completion service
```python
from semantic_kernel.connectors.ai.nvidia import NvidiaChatCompletion

chat_service = NvidiaChatCompletion(
    ai_model_id="meta/llama-3.1-8b-instruct", # Default model if not specified
    api_key="your-nvidia-api-key", # Can also use NVIDIA_API_KEY env variable
    service_id="nvidia-chat" # Optional service identifier
)
kernel.add_service(chat_service)
```

### Basic chat completion
```python
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole

chat_history = ChatHistory()
chat_history.add_message(AuthorRole.USER, "Hello, how are you?")
response = await kernel.get_service("nvidia-chat").get_chat_message_content(chat_history)
print(response.content)
```

### Using with Chat Completion Agent
```python
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.nvidia import NvidiaChatCompletion

agent = ChatCompletionAgent(
    service=NvidiaChatCompletion(),
    name="SK-Assistant",
    instructions="You are a helpful assistant.",
)
response = await agent.get_response(messages="Write a haiku about Semantic Kernel.")
print(response.content)
```

