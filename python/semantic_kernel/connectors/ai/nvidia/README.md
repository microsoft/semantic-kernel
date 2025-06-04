# semantic_kernel.connectors.ai.nvidia

This connector enables integration with NVIDIA NIM API for text embeddings. It allows you to use NVIDIA's embedding models within the Semantic Kernel framework.

## Quick start

### Initialize the kernel
```python
import semantic_kernel as sk
kernel = sk.Kernel()
```

### Add NVIDIA text embedding service
You can provide your API key directly or through environment variables
```python
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
