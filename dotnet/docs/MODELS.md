# Models

This document describes the planned models to be supported by Semantic Kernel along with their current status. If you are interested in contributing to the development of a model, please use the attached links to the GitHub issues and comment that you're wanting to help.

## Supported deployment types

In the core Semantic Kernel repo, we plan on supporting up to four deployment types of each model:

- Dedicated API endpoints (e.g., OpenAI's APIs, Mistral.AI, and Google Gemini)
- Azure AI deployments via the [model catalog](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/model-catalog)
- Local deployments via [Ollama](https://ollama.ai/library)
- Hugging face deployment using the [Hugging Face inference API](https://huggingface.co/docs/api-inference/index)

To support these different deployment types, we will follow a similar pattern to the Azure OpenAI and OpenAI connectors. Each connector uses the same underlying model and abstractions, but the connector constructors may take different parameters. For example, the Azure OpenAI connector expects an Azure endpoint and key, whereas the OpenAI connector expects an OpenAI organization ID and API key.

If there is another deployment type you'd like to see supported, please open an issue. We'll either work with you to add support for it or help you create a custom repository and NuGet package for your use case.

## Planned models

The following models are currently prioritized for development. If you'd like to see a model added to this list, please open an issue. If you'd like to contribute to the development of a model, please comment on the issue that you're wanting to help.

Please note that not all of the model interfaces are defined yet. As part of contributing a new model, we'll work with you to define the interface and then implement it. As part of implementing the connector, you may also determine that the currently planned interface isn't the best fit for the model. If that's the case, we'll work with you to update the interface.

### OpenAI

| Priority | Model                   | Status      | Interface                      | Deployment type | GitHub issue | Developer   | Reviewer |
| -------- | ----------------------- | ----------- | ------------------------------ | --------------- | ------------ | ----------- | -------- |
| P0       | GPT-3.5-turbo           | Complete    | `IChatCompletion`              | OpenAI API      | N/A          | N/A         | N/A      |
| P0       | GPT-3.5-turbo           | Complete    | `IChatCompletion`              | Azure AI        | N/A          | N/A         | N/A      |
| P0       | GPT-4                   | Complete    | `IChatCompletion`              | OpenAI API      | N/A          | N/A         | N/A      |
| P0       | GPT-4                   | Complete    | `IChatCompletion`              | Azure AI        | N/A          | N/A         | N/A      |
| P0       | GPT-4v                  | Complete    | `IChatCompletion`              | OpenAI API      | N/A          | N/A         | N/A      |
| P0       | GPT-4v                  | Complete    | `IChatCompletion`              | Azure AI        | N/A          | N/A         | N/A      |
| P0       | text-embedding-ada-002  | Preview     | `IEmbeddingGeneration`         | OpenAI API      | N/A          | N/A         | N/A      |
| P0       | text-embedding-ada-002  | Preview     | `IEmbeddingGeneration`         | Azure AI        | N/A          | N/A         | N/A      |
| P0       | DALL·E 3                | Preview     | `ITextToImage`                 | OpenAI API      | N/A          | N/A         | N/A      |
| P0       | DALL·E 3                | Preview     | `ITextToImage`                 | Azure AI        | N/A          | N/A         | N/A      |
| P0       | Text-to-speech          | Complete    | `ITextToSpeech`                | OpenAI API      | TBD          | dmytrostruk | TBD      |
| P0       | Speech-to-text          | Complete    | `ISpeechRecognition`           | OpenAI API      | TBD          | dmytrostruk | TBD      |
| P1       | openai-whisper-large-v3 | Not started | `ISpeechRecognition`           | Azure AI        | TBD          | TBD         | TBD      |
| P1       | openai-whisper-large-v3 | Not started | `ISpeechRecognition`           | Hugging Face    | TBD          | TBD         | TBD      |
| P2       | Moderation              | In Progress | `ITextClassification`          | OpenAI API      | #5062        | Krzysztof318 | MarkWallace |
| P2       | clip-vit-base-patch32   | Not started | `IZeroShotImageClassification` | Azure AI        | TBD          | TBD         | TBD      |
| P2       | clip-vit-base-patch32   | Not started | `IZeroShotImageClassification` | Hugging Face    | TBD          | TBD         | TBD      |

### Microsoft

| Priority | Model             | Status      | Interface              | Deployment type | GitHub issue | Developer | Reviewer |
| -------- | ----------------- | ----------- | ---------------------- | --------------- | ------------ | --------- | -------- |
| P0       | microsoft-phi-1-5 | Not started | `ITextGeneration`      | Azure AI        | TBD          | TBD       | TBD      |
| P0       | microsoft-phi-1-5 | Not started | `ITextGeneration`      | Hugging Face    | TBD          | TBD       | TBD      |
| P0       | microsoft-phi-2   | Not started | `ITextGeneration`      | Azure AI        | TBD          | TBD       | TBD      |
| P0       | microsoft-phi-2   | Not started | `ITextGeneration`      | Hugging Face    | TBD          | TBD       | TBD      |
| P2       | resnet-50         | Not started | `IImageClassification` | Azure AI        | TBD          | TBD       | TBD      |
| P2       | resnet-50         | Not started | `IImageClassification` | Hugging Face    | TBD          | TBD       | TBD      |

### Google

| Priority | Model             | Status      | Interface              | Deployment type | GitHub issue | Developer    | Reviewer     |
| -------- | ----------------- | ----------- | ---------------------- | --------------- | ------------ | ------------ | ------------ |
| P0       | gemini-pro        | In Progress | `IChatCompletion`      | Google API      | TBD          | Krzysztof318 | RogerBarreto |
| P0       | gemini-pro-vision | In Progress | `IChatCompletion`      | Google API      | TBD          | Krzysztof318 | RogerBarreto |
| P0       | gemini-ultra      | In Progress | `IChatCompletion`      | Google API      | TBD          | Krzysztof318 | RogerBarreto |
| P0       | embedding-001     | In Progress | `IEmbeddingGeneration` | Google API      | TBD          | Krzysztof318 | RogerBarreto |

### Facebook

| Priority | Model                     | Status      | Interface         | Deployment type | GitHub issue | Developer | Reviewer |
| -------- | ------------------------- | ----------- | ----------------- | --------------- | ------------ | --------- | -------- |
| P0       | Llama-2-7b-chat           | Not started | `IChatCompletion` | Azure AI        | TBD          | TBD       | TBD      |
| P0       | Llama-2-7b-chat           | Not started | `IChatCompletion` | Hugging Face    | TBD          | TBD       | TBD      |
| P0       | Llama-2-13b-chat          | Not started | `IChatCompletion` | Azure AI        | TBD          | TBD       | TBD      |
| P0       | Llama-2-13b-chat          | Not started | `IChatCompletion` | Hugging Face    | TBD          | TBD       | TBD      |
| P0       | Llama-2-70b-chat          | Not started | `IChatCompletion` | Azure AI        | TBD          | TBD       | TBD      |
| P0       | Llama-2-70b-chat          | Not started | `IChatCompletion` | Hugging Face    | TBD          | TBD       | TBD      |
| P0       | CodeLlama-7b-Instruct-hf  | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P0       | CodeLlama-7b-Instruct-hf  | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |
| P0       | CodeLlama-13b-Instruct-hf | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P0       | CodeLlama-13b-Instruct-hf | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |
| P0       | CodeLlama-34b-Instruct-hf | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P0       | CodeLlama-34b-Instruct-hf | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |
| P1       | Llama-2-7b                | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P1       | Llama-2-7b                | Not started | `ITextGeneration` | Ollama          | TBD          | TBD       | TBD      |
| P1       | Llama-2-7b                | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |
| P1       | Llama-2-13b               | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P1       | Llama-2-13b               | Not started | `ITextGeneration` | Ollama          | TBD          | TBD       | TBD      |
| P1       | Llama-2-13b               | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |
| P1       | Llama-2-70b               | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P1       | Llama-2-70b               | Not started | `ITextGeneration` | Ollama          | TBD          | TBD       | TBD      |
| P1       | Llama-2-70b               | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |
| P1       | CodeLlama-7b-hf           | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P1       | CodeLlama-7b-hf           | Not started | `ITextGeneration` | Ollama          | TBD          | TBD       | TBD      |
| P1       | CodeLlama-7b-hf           | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |
| P1       | CodeLlama-13b-hf          | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P1       | CodeLlama-13b-hf          | Not started | `ITextGeneration` | Ollama          | TBD          | TBD       | TBD      |
| P1       | CodeLlama-13b-hf          | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |
| P1       | CodeLlama-34b-hf          | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P1       | CodeLlama-34b-hf          | Not started | `ITextGeneration` | Ollama          | TBD          | TBD       | TBD      |
| P1       | CodeLlama-34b-hf          | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |
| P1       | CodeLlama-7b-Python-hf    | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P1       | CodeLlama-7b-Python-hf    | Not started | `ITextGeneration` | Ollama          | TBD          | TBD       | TBD      |
| P2       | CodeLlama-7b-Python-hf    | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |
| P2       | CodeLlama-13b-Python-hf   | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P2       | CodeLlama-13b-Python-hf   | Not started | `ITextGeneration` | Ollama          | TBD          | TBD       | TBD      |
| P2       | CodeLlama-13b-Python-hf   | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |
| P2       | CodeLlama-34b-Python-hf   | Not started | `ITextGeneration` | Azure AI        | TBD          | TBD       | TBD      |
| P2       | CodeLlama-34b-Python-hf   | Not started | `ITextGeneration` | Ollama          | TBD          | TBD       | TBD      |
| P2       | CodeLlama-34b-Python-hf   | Not started | `ITextGeneration` | Hugging Face    | TBD          | TBD       | TBD      |

### Mistral

| Priority | Model                   | Status      | Interface         | Deployment type | GitHub issue | Developer | Reviewer |
| -------- | ----------------------- | ----------- | ----------------- | --------------- | ------------ | --------- | -------- |
| P2       | Mistral-7B-v0.2         | Not started | `IChatCompletion` | Mistral API     | TBD          | TBD       | TBD      |
| P2       | Mistral-7B-v0.2         | Not started | `IChatCompletion` | Ollama          | TBD          | TBD       | TBD      |
| P2       | Mistral-7B-v0.1         | Not started | `IChatCompletion` | Azure AI        | TBD          | TBD       | TBD      |
| P2       | Mistral-7B-v0.1         | Not started | `IChatCompletion` | Hugging Face    | TBD          | TBD       | TBD      |
| P2       | Mistral-7B-Instruct-v01 | Not started | `IChatCompletion` | Azure AI        | TBD          | TBD       | TBD      |
| P2       | Mistral-7B-Instruct-v01 | Not started | `IChatCompletion` | Hugging Face    | TBD          | TBD       | TBD      |
| P2       | Mixtral-8X7B-v0.1       | Not started | `IChatCompletion` | Mistral API     | TBD          | TBD       | TBD      |
| P2       | Mixtral-8X7B-v0.1       | Not started | `IChatCompletion` | Azure AI        | TBD          | TBD       | TBD      |
| P2       | Mixtral-8X7B-v0.1       | Not started | `IChatCompletion` | Hugging Face    | TBD          | TBD       | TBD      |
| P2       | mistral-medium          | Not started | `IChatCompletion` | Mistral API     | TBD          | TBD       | TBD      |
| P2       | mistral-embed           | Not started | `IChatCompletion` | Mistral API     | TBD          | TBD       | TBD      |

### Other

| Priority | Model                          | Status      | Interface            | Deployment type | GitHub issue | Developer | Reviewer |
| -------- | ------------------------------ | ----------- | -------------------- | --------------- | ------------ | --------- | -------- |
| P0       | wav2vec2-large-xlsr-53-english | Not started | `ISpeechRecognition` | Azure AI        | TBD          | TBD       | TBD      |
| P1       | wav2vec2-large-xlsr-53-english | Not started | `ISpeechRecognition` | Hugging Face    | TBD          | TBD       | TBD      |
| P2       | bert-base-uncased              | Not started | `IFillMask`          | Azure AI        | TBD          | TBD       | TBD      |
| P2       | bert-base-uncased              | Not started | `IFillMask`          | Hugging Face    | TBD          | TBD       | TBD      |
| P2       | roberta-large                  | Not started | `IFillMask`          | Azure AI        | TBD          | TBD       | TBD      |
| P2       | roberta-large                  | Not started | `IFillMask`          | Hugging Face    | TBD          | TBD       | TBD      |
| P1       | stable-diffusion-xl-base-1.0   | Not started | `ITextToImage`       | Azure AI        | TBD          | TBD       | TBD      |
| P1       | stable-diffusion-xl-base-1.0   | Not started | `ITextToImage`       | Hugging Face    | TBD          | TBD       | TBD      |
