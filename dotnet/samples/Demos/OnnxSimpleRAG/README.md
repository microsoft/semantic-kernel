# Onnx Simple RAG (Retrieval Augmented Generation) Sample

This sample demonstrates how you can do RAG using Semantic Kernel with the ONNX Connector that enables running Local Models straight from files. 

In this example we setup two ONNX AI Services:
- Chat Completion with [Microsoft's Phi-3-ONNX](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-onnx) model 
- Text Embeddings with [Taylor's BGE Micro V2](https://huggingface.co/TaylorAI/bge-micro-v2) for embeddings to enable RAG for user queries.

> [!IMPORTANT]
> You can modify to use any other combination of models enabled for ONNX runtime.

## Semantic Kernel used Features

- [Chat Completion Service](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/IChatCompletionService.cs) - Using the Chat Completion Service from [Onnx Connector](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.Onnx/OnnxRuntimeGenAIChatCompletionService.cs) to generate responses from the Local Model.
- [Text Embeddings Generation Service]() - Using the Text Embeddings Generation Service from [Onnx Connector](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.Onnx/BertOnnxTextEmbeddingGenerationService.cs) to generate
- [Vector Store](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/VectorData.Abstractions/VectorStorage/IVectorStore.cs) Using Vector Store Service with [InMemoryVectorStore](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.Memory.InMemory/InMemoryVectorStore.cs) to store and retrieve embeddings in memory for RAG.
- [Semantic Text Memory](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Core/Memory/SemanticTextMemory.cs) to manage the embeddings in memory for RAG.
- [Text Memory Plugin](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Plugins/Plugins.Memory/TextMemoryPlugin.cs) to enable memory retrieval functions (Recall) to be used with Prompts for RAG.

## Prerequisites

- [.NET 8](https://dotnet.microsoft.com/download/dotnet/8.0).

## 1. Configuring the sample

### Downloading the Models

For this example we chose Hugging Face as our repository for download of the local models, go to a directory of your choice where the models should be downloaded and run the following commands:

```powershell
git clone https://huggingface.co/TaylorAI/bge-micro-v2
git clone https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-onnx
```

> [!IMPORTANT]
> Both `BGE-Micro-V2` and `Phi-3` models are too large to be downloaded by the `git clone` command alone if you don't have [git-lfs extension](https://git-lfs.com/) installed, for this you may need to download the models manually and overwrite the files in the cloned directories.

- Manual download [BGE-Micro-V2](https://huggingface.co/TaylorAI/bge-micro-v2/resolve/main/onnx/model.onnx?download=true) (69 MB)
- Manual download [Phi-3-Mini-4k CPU](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-onnx/resolve/main/cpu_and_mobile/cpu-int4-rtn-block-32/phi3-mini-4k-instruct-cpu-int4-rtn-block-32.onnx.data?download=true) (≈2.7 GB)

Update the `Program.cs` file lines below with the paths to the models you downloaded in the previous step.

```csharp
// Path to the folder of your downloaded ONNX PHI-3 model
var chatModelPath = @"C:\path\to\huggingface\Phi-3-mini-4k-instruct-onnx\cpu_and_mobile\cpu-int4-rtn-block-32";

// Path to the file of your downloaded ONNX BGE-MICRO-V2 model
var embeddingModelPath = @"C:\path\to\huggingface\bge-micro-v2\onnx\model.onnx";

// Path to the vocab file your ONNX BGE-MICRO-V2 model
var embeddingVocabPath = @"C:\path\to\huggingface\bge-micro-v2\vocab.txt";
```

**Optional**: Change or add any fact text you want your AI to know about to the `facts` list in the `Program.cs` file.

```csharp
foreach (var fact in new[] {
    "My fact 1.",
    "My fact 2." })
{
```

## Configuring the sample

The sample can be configured by using the command line with .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) to avoid the risk of leaking secrets into the repository, branches and pull requests.

### Using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)

```powershell
dotnet user-secrets set "Onnx:ModelId" ".. Onnx model id" (default: phi-3)
dotnet user-secrets set "Onnx:ModelPath" ".. your Onnx model folder path .." 
dotnet user-secrets set "Onnx:EmbeddingModelPath" ".. your Onnx model file path .."
dotnet user-secrets set "Onnx:EmbeddingVocabPath" ".. your Onnx model vocab file path .."
```

## 3. Running the sample

After configuring the sample, to build and run the console application just hit `F5`.

To build and run the console application from the terminal use the following commands:

```powershell
dotnet build
dotnet run
```

Ask to the Model any question you want, the AI will try to answer based on the facts you provided.

### Example of a conversation

> **User** > What is semantic kernel SDK used for?

> **Assistant** > The Semantic Kernel SDK is used for developing AI agents and integrating the latest AI models into your C#, Python, or Java codebase. It acts as a lightweight, open-source development kit that facilitates the creation of AI applications with enterprise-grade capabilities. By serving as an efficient middleware, it allows for the rapid development and deployment of AI solutions across various programming environments.

> **User** > When should I use Kernel Memory?

> **Assistant** > Kernel Memory is best suited for tasks that involve large-scale continuous data, require efficient indexing and processing, and benefit from the integration of retrieval-based and generative models, synthetic memory, prompt engineering, and custom semantic memory processing.
