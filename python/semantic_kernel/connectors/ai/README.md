# AI Connectors

This directory contains the implementation of the AI connectors (aka AI services) that are used to interact with AI models.

Depending on the modality, the AI connector can inherit from one of the following classes:

- [`ChatCompletionClientBase`](./chat_completion_client_base.py) for chat completion tasks.
- [`TextCompletionClientBase`](./text_completion_client_base.py) for text completion tasks.
- [`AudioToTextClientBase`](./audio_to_text_client_base.py) for audio to text tasks.
- [`TextToAudioClientBase`](./text_to_audio_client_base.py) for text to audio tasks.
- [`TextToImageClientBase`](./text_to_image_client_base.py) for text to image tasks.
- [`EmbeddingGeneratorBase`](./embeddings/embedding_generator_base.py) for text embedding tasks.

All base clients inherit from the [`AIServiceClientBase`](../../services/ai_service_client_base.py) class.

## Existing AI connectors

| Services          | Connectors                          |
|-------------------------|--------------------------------------|
| OpenAI     | [`OpenAIChatCompletion`](./open_ai/services/open_ai_chat_completion.py) |
|            | [`OpenAITextCompletion`](./open_ai/services/open_ai_text_completion.py) |
|            | [`OpenAITextEmbedding`](./open_ai/services/open_ai_text_embedding.py) |
|            | [`OpenAITextToImage`](./open_ai/services/open_ai_text_to_image.py) |
|            | [`OpenAITextToAudio`](./open_ai/services/open_ai_text_to_audio.py) |
|            | [`OpenAIAudioToText`](./open_ai/services/open_ai_audio_to_text.py) |
| Azure OpenAI | [`AzureChatCompletion`](./open_ai/services/azure_chat_completion.py) |
|            | [`AzureTextCompletion`](./open_ai/services/azure_text_completion.py) |
|            | [`AzureTextEmbedding`](./open_ai/services/azure_text_embedding.py) |
|            | [`AzureTextToImage`](./open_ai/services/azure_text_to_image.py) |
|            | [`AzureTextToAudio`](./open_ai/services/azure_text_to_audio.py) |
|            | [`AzureAudioToText`](./open_ai/services/azure_audio_to_text.py) |
| Azure AI Inference | [`AzureAIInferenceChatCompletion`](./azure_ai_inference/services/azure_ai_inference_chat_completion.py) |
|            | [`AzureAIInferenceTextEmbedding`](./azure_ai_inference/services/azure_ai_inference_text_embedding.py) |
| Anthropic | [`AnthropicChatCompletion`](./anthropic/services/anthropic_chat_completion.py) |
| [Bedrock](./bedrock/README.md) | [`BedrockChatCompletion`](./bedrock/services/bedrock_chat_completion.py) |
|         | [`BedrockTextCompletion`](./bedrock/services/bedrock_text_completion.py) |
|         | [`BedrockTextEmbedding`](./bedrock/services/bedrock_text_embedding.py) |
| [Google AI](./google/README.md) | [`GoogleAIChatCompletion`](./google/google_ai/services/google_ai_chat_completion.py) |
|           | [`GoogleAITextCompletion`](./google/google_ai/services/google_ai_text_completion.py) |
|           | [`GoogleAITextEmbedding`](./google/google_ai/services/google_ai_text_embedding.py) |
| [Vertex AI](./google/README.md) | [`VertexAIChatCompletion`](./google/vertex_ai/services/vertex_ai_chat_completion.py) |
|           | [`VertexAITextCompletion`](./google/vertex_ai/services/vertex_ai_text_completion.py) |
|           | [`VertexAITextEmbedding`](./google/vertex_ai/services/vertex_ai_text_embedding.py) |
| HuggingFace | [`HuggingFaceTextCompletion`](./hugging_face/services/hf_text_completion.py) |
|             | [`HuggingFaceTextEmbedding`](./hugging_face/services/hf_text_embedding.py) |
| Mistral AI | [`MistralAIChatCompletion`](./mistral_ai/services/mistral_ai_chat_completion.py) |
|            | [`MistralAITextEmbedding`](./mistral_ai/services/mistral_ai_text_embedding.py) |
| Ollama | [`OllamaChatCompletion`](./ollama/services/ollama_chat_completion.py) |
|        | [`OllamaTextCompletion`](./ollama/services/ollama_text_completion.py) |
|        | [`OllamaTextEmbedding`](./ollama/services/ollama_text_embedding.py) |
| Onnx | [`OnnxGenAIChatCompletion`](./onnx/services/onnx_gen_ai_chat_completion.py) |
|      | [`OnnxGenAITextCompletion`](./onnx/services/onnx_gen_ai_text_completion.py) |