# Semantic Kernel Concepts by Feature

This section contains code snippets that demonstrate the usage of Semantic Kernel features.

| Features | Description |
| -------- | ----------- |
| Functions | Invoking [`Method`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Core/Functions/KernelFunctionFromMethod.cs) or [`Prompt`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Core/Functions/KernelFunctionFromPrompt.cs) functions with [`Kernel`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/Kernel.cs) |
| Chat Completion | Using [`ChatCompletion`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/IChatCompletionService.cs) messaging capable service with models  |
| Text Generation | Using [`TextGeneration`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/TextGeneration/ITextGenerationService.cs) capable service with models  |
| Text to Image | Using [`TextToImage`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/TextToImage/ITextToImageService.cs) services to generate images |
| Image to Text | Using [`ImageToText`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ImageToText/IImageToTextService.cs) services to describe images |
| Text to Audio | Using [`TextToAudio`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/TextToAudio/ITextToAudioService.cs) services to generate audio |  
| Audio to Text | Using [`AudioToText`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/AudioToText/IAudioToTextService.cs) services to describe audio | 
| Telemetry | Code examples how to setup and use [`Telemetry`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/docs/TELEMETRY.md) |
| Logging | Code examples how to setup and use [`Logging`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/docs/TELEMETRY.md#logging) |
| Dependency Injection | Examples on using `DI Container` with SK  |
| Plugins | Different ways of creating and using [`Plugins`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/Functions/KernelPlugin.cs) |
| Auto Function Calling | Using `Auto Function Calling` to allow function call capable models to invoke Kernel Functions automatically |
| Filters | Different ways of filtering with Kernel |
| Memory | Using [`Memory`](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/SemanticKernel.Abstractions/Memory) AI concepts |
| Search | Using search services information |
| Templates | Using [`Templates`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/PromptTemplate/IPromptTemplate.cs) with parametrization for `Prompt` rendering  |
| RAG | Different ways of `RAG` (Retrieval-Augmented Generation) |
| Local Models | Using services against `LocalModels` to run models locally |
| Agents | Different ways of using [`Agents`](./AgentSyntax/README.md)  |
| <strike>AgentSyntax</strike> | ⚠️ Work in progress: Moving into [`Agents`](./AgentSyntax/README.md).    |