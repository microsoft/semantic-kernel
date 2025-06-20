# 按功能划分的 Semantic Kernel 概念

[English](README.md) | [Chinese](README.zh-CN.md)

下方是一些代码片段，展示了许多 Semantic Kernel 功能的使用方法。

## 运行测试

```text
dotnet test -l "console;verbosity=detailed" --filter "FullyQualifiedName=NameSpace.TestClass.TestMethod"
```

Example for `ChatCompletion/OpenAI_ChatCompletion.cs` file, targeting the `ChatPromptSync` test:

```powershell
dotnet test -l "console;verbosity=detailed" --filter "FullyQualifiedName=ChatCompletion.OpenAI_ChatCompletion.ChatPromptAsync"
```

## 目录

### Agents - 不同方式使用 [`Agents`](./Agents/README.md)

- [ComplexChat_NestedShopper](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Agents/ComplexChat_NestedShopper.cs)
- [MixedChat_Agents](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Agents/MixedChat_Agents.cs)
- [OpenAIAssistant_ChartMaker](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Agents/OpenAIAssistant_ChartMaker.cs)
- [ChatCompletion_Rag: Shows how to easily add RAG to an agent](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Agents/ChatCompletion_Rag.cs)
- [ChatCompletion_Mem0: Shows how to add memory to an agent using mem0](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Agents/ChatCompletion_Mem0.cs)
- [ChatCompletion_Whiteboard: Shows how to add short term Whiteboarding memory to an agent](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Agents/ChatCompletion_Whiteboard.cs)
- [ChatCompletion_ContextualFunctionSelection: Shows how to add contextual function selection capabilities to an agent](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Agents/ChatCompletion_ContextualFunctionSelection.cs)

### AudioToText - 使用 [`AudioToText`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/AudioToText/IAudioToTextService.cs) 服务从音频中提取文本的不同方式

- [OpenAI_AudioToText](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/AudioToText/OpenAI_AudioToText.cs)

### FunctionCalling - 使用支持函数调用的模型进行 `Function Calling` 的示例

- [FunctionCalling](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/FunctionCalling/FunctionCalling.cs)
- [FunctionCalling_ReturnMetadata](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/FunctionCalling/FunctionCalling_ReturnMetadata.cs)
- [Gemini_FunctionCalling](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/FunctionCalling/Gemini_FunctionCalling.cs)
- [AzureAIInference_FunctionCalling](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/FunctionCalling/AzureAIInference_FunctionCalling.cs)
- [NexusRaven_HuggingFaceTextGeneration](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/FunctionCalling/NexusRaven_FunctionCalling.cs)
- [MultipleFunctionsVsParameters](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/FunctionCalling/MultipleFunctionsVsParameters.cs)
- [FunctionCalling_SharedState](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/FunctionCalling/FunctionCalling_SharedState.cs)

### Caching - 缓存实现的示例

- [SemanticCachingWithFilters](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Caching/SemanticCachingWithFilters.cs)

### ChatCompletion - 使用 [`ChatCompletion`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/IChatCompletionService.cs) 消息服务的示例

- [AzureAIInference_ChatCompletion](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/AzureAIInference_ChatCompletion.cs)
- [AzureAIInference_ChatCompletionStreaming](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/AzureAIInference_ChatCompletionStreaming.cs)
- [AzureOpenAI_ChatCompletion](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/AzureOpenAI_ChatCompletion.cs)
- [AzureOpenAI_ChatCompletionWithReasoning](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/AzureOpenAI_ChatCompletionWithReasoning.cs)
- [AzureOpenAI_ChatCompletionStreaming](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/AzureOpenAI_ChatCompletionStreaming.cs)
- [AzureOpenAI_CustomClient](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/AzureOpenAI_CustomClient.cs)
- [AzureOpenAIWithData_ChatCompletion](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/AzureOpenAIWithData_ChatCompletion.cs)
- [ChatHistoryAuthorName](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/ChatHistoryAuthorName.cs)
- [ChatHistoryInFunctions](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/ChatHistoryInFunctions.cs)
- [ChatHistorySerialization](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/ChatHistorySerialization.cs)
- [Connectors_CustomHttpClient](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Connectors_CustomHttpClient.cs)
- [Connectors_KernelStreaming](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Connectors_KernelStreaming.cs)
- [Connectors_WithMultipleLLMs](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Connectors_WithMultipleLLMs.cs)
- [Google_GeminiChatCompletion](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Google_GeminiChatCompletion.cs)
- [Google_GeminiChatCompletionStreaming](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Google_GeminiChatCompletionStreaming.cs)
- [Google_GeminiChatCompletionWithThinkingBudget](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Google_GeminiChatCompletionWithThinkingBudget.cs)
- [Google_GeminiGetModelResult](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Google_GeminiGetModelResult.cs)
- [Google_GeminiStructuredOutputs](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Google_GeminiStructuredOutputs.cs)
- [Google_GeminiVision](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Google_GeminiVision.cs)
- [HuggingFace_ChatCompletion](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/HuggingFace_ChatCompletion.cs)
- [HuggingFace_ChatCompletionStreaming](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/HuggingFace_ChatCompletionStreaming.cs)
- [HybridCompletion_Fallback](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/HybridCompletion_Fallback.cs)
- [LMStudio_ChatCompletion](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/LMStudio_ChatCompletion.cs)
- [LMStudio_ChatCompletionStreaming](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/LMStudio_ChatCompletionStreaming.cs)
- [MistralAI_ChatCompletion](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/MistralAI_ChatCompletion.cs)
- [MistralAI_ChatPrompt](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/MistralAI_ChatPrompt.cs)
- [MistralAI_FunctionCalling](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/MistralAI_FunctionCalling.cs)
- [MistralAI_StreamingFunctionCalling](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/MistralAI_StreamingFunctionCalling.cs)
- [MultipleProviders_ChatHistoryReducer](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/MultipleProviders_ChatHistoryReducer.cs)
- [Ollama_ChatCompletion](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Ollama_ChatCompletion.cs)
- [Ollama_ChatCompletionStreaming](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Ollama_ChatCompletionStreaming.cs)
- [Ollama_ChatCompletionWithVision](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Ollama_ChatCompletionWithVision.cs)
- [Onnx_ChatCompletion](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Onnx_ChatCompletion.cs)
- [Onnx_ChatCompletionStreaming](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/Onnx_ChatCompletionStreaming.cs)
- [OpenAI_ChatCompletion](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_ChatCompletion.cs)
- [OpenAI_ChatCompletionStreaming](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_ChatCompletionStreaming.cs)
- [OpenAI_ChatCompletionWebSearch](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_ChatCompletionWebSearch.cs)
- [OpenAI_ChatCompletionWithAudio](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_ChatCompletionWithAudio.cs)
- [OpenAI_ChatCompletionWithFile](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_ChatCompletionWithFile.cs)
- [OpenAI_ChatCompletionWithReasoning](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_ChatCompletionWithReasoning.cs)
- [OpenAI_ChatCompletionWithVision](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_ChatCompletionWithVision.cs)
- [OpenAI_CustomClient](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_CustomClient.cs)
- [OpenAI_FunctionCalling](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_FunctionCalling.cs)
- [OpenAI_FunctionCallingWithMemoryPlugin](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_FunctionCallingWithMemoryPlugin.cs)
- [OpenAI_ReasonedFunctionCalling](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_ReasonedFunctionCalling.cs)
- [OpenAI_RepeatedFunctionCalling](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_RepeatedFunctionCalling.cs)
- [OpenAI_StructuredOutputs](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_StructuredOutputs.cs)
- [OpenAI_UsingLogitBias](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_UsingLogitBias.cs)

### DependencyInjection - 使用 `DI 容器` 的示例

- [HttpClient_Registration](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/DependencyInjection/HttpClient_Registration.cs)
- [HttpClient_Resiliency](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/DependencyInjection/HttpClient_Resiliency.cs)
- [Kernel_Building](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/DependencyInjection/Kernel_Building.cs)
- [Kernel_Injecting](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/DependencyInjection/Kernel_Injecting.cs)

### Filtering - 不同的过滤方式

- [AutoFunctionInvocationFiltering](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Filtering/AutoFunctionInvocationFiltering.cs)
- [FunctionInvocationFiltering](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Filtering/FunctionInvocationFiltering.cs)
- [MaxTokensWithFilters](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Filtering/MaxTokensWithFilters.cs)
- [PIIDetection](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Filtering/PIIDetection.cs)
- [PromptRenderFiltering](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Filtering/PromptRenderFiltering.cs)
- [RetryWithFilters](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Filtering/RetryWithFilters.cs)
- [TelemetryWithFilters](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Filtering/TelemetryWithFilters.cs)
- [AzureOpenAI_DeploymentSwitch](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Filtering/AzureOpenAI_DeploymentSwitch.cs)

### Functions - 使用 [`Method`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Core/Functions/KernelFunctionFromMethod.cs) 或 [`Prompt`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Core/Functions/KernelFunctionFromPrompt.cs) 函数通过 [`Kernel`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/Kernel.cs) 调用

- [Arguments](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Functions/Arguments.cs)
- [FunctionResult_Metadata](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Functions/FunctionResult_Metadata.cs)
- [FunctionResult_StronglyTyped](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Functions/FunctionResult_StronglyTyped.cs)
- [MethodFunctions](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Functions/MethodFunctions.cs)
- [MethodFunctions_Advanced](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Functions/MethodFunctions_Advanced.cs)
- [MethodFunctions_Types](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Functions/MethodFunctions_Types.cs)
- [MethodFunctions_Yaml](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Functions/MethodFunctions_Yaml.cs)
- [PromptFunctions_Inline](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Functions/PromptFunctions_Inline.cs)
- [PromptFunctions_MultipleArguments](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Functions/PromptFunctions_MultipleArguments.cs)

### ImageToText - 使用 [`ImageToText`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ImageToText/IImageToTextService.cs) 服务描述图像

- [HuggingFace_ImageToText](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ImageToText/HuggingFace_ImageToText.cs)

### Memory - 使用 AI [`Memory`](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/SemanticKernel.Abstractions/Memory) 概念

- [AWSBedrock_EmbeddingGeneration](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/AWSBedrock_EmbeddingGeneration.cs)
- [OpenAI_EmbeddingGeneration](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/OpenAI_EmbeddingGeneration.cs)
- [Ollama_EmbeddingGeneration](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/Ollama_EmbeddingGeneration.cs)
- [Onnx_EmbeddingGeneration](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/Onnx_EmbeddingGeneration.cs)
- [HuggingFace_EmbeddingGeneration](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/HuggingFace_EmbeddingGeneration.cs)
- [TextChunkerUsage](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/TextChunkerUsage.cs)
- [TextChunkingAndEmbedding](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/TextChunkingAndEmbedding.cs)
- [VectorStore_DataIngestion_Simple: A simple example of how to do data ingestion into a vector store when getting started.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_DataIngestion_Simple.cs)
- [VectorStore_DataIngestion_MultiStore: An example of data ingestion that uses the same code to ingest into multiple vector stores types.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_DataIngestion_MultiStore.cs)
- [VectorStore_DataIngestion_CustomMapper: An example that shows how to use a custom mapper for when your data model and storage model doesn't match.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_DataIngestion_CustomMapper.cs)
- [VectorStore_VectorSearch_Simple: A simple example of how to do data ingestion into a vector store and then doing a vector similarity search over the data.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_VectorSearch_Simple.cs)
- [VectorStore_VectorSearch_Paging: An example showing how to do vector search with paging.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_VectorSearch_Paging.cs)
- [VectorStore_VectorSearch_MultiVector: An example showing how to pick a target vector when doing vector search on a record that contains multiple vectors.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_VectorSearch_MultiVector.cs)
- [VectorStore_VectorSearch_MultiStore_Common: An example showing how to write vector database agnostic code with different vector databases.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_VectorSearch_MultiStore_Common.cs)
- [VectorStore_HybridSearch_Simple_AzureAISearch: An example showing how to do hybrid search using AzureAISearch.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_HybridSearch_Simple_AzureAISearch.cs)
- [VectorStore_DynamicDataModel_Interop: An example that shows how you can use dynamic data modeling from Semantic Kernel to read and write to a Vector Store.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_DynamicDataModel_Interop.cs)
- [VectorStore_ConsumeFromMemoryStore_AzureAISearch: An example that shows how you can use the AzureAISearchVectorStore to consume data that was ingested using the AzureAISearchMemoryStore.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_ConsumeFromMemoryStore_AzureAISearch.cs)
- [VectorStore_ConsumeFromMemoryStore_Qdrant: An example that shows how you can use the QdrantVectorStore to consume data that was ingested using the QdrantMemoryStore.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_ConsumeFromMemoryStore_Qdrant.cs)
- [VectorStore_ConsumeFromMemoryStore_Redis: An example that shows how you can use the RedisVectorStore to consume data that was ingested using the RedisMemoryStore.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_ConsumeFromMemoryStore_Redis.cs)
- [VectorStore_Langchain_Interop: An example that shows how you can use various Vector Store to consume data that was ingested using Langchain.](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Memory/VectorStore_Langchain_Interop.cs)

### Optimization - 不同成本和性能优化技术的示例

- [FrugalGPTWithFilters](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Optimization/FrugalGPTWithFilters.cs)
- [PluginSelectionWithFilters](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Optimization/PluginSelectionWithFilters.cs)

### Planners - 使用 `Planners` 的示例

- [AutoFunctionCallingPlanning](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Planners/AutoFunctionCallingPlanning.cs)
- [FunctionCallStepwisePlanning](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Planners/FunctionCallStepwisePlanning.cs)
- [HandlebarsPlanning](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Planners/HandlebarsPlanning.cs)

### Plugins - 创建和使用 [`Plugins`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/Functions/KernelPlugin.cs) 的不同方式

- [ApiManifestBasedPlugins](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/ApiManifestBasedPlugins.cs)
- [ConversationSummaryPlugin](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/ConversationSummaryPlugin.cs)
- [CreatePluginFromOpenApiSpec_Github](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/CreatePluginFromOpenApiSpec_Github.cs)
- [CreatePluginFromOpenApiSpec_Jira](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/CreatePluginFromOpenApiSpec_Jira.cs)
- [CreatePluginFromOpenApiSpec_Klarna](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/CreatePluginFromOpenApiSpec_Klarna.cs)
- [CreatePluginFromOpenApiSpec_RepairService](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/CreatePluginFromOpenApiSpec_RepairService.cs)
- [CreatePromptPluginFromDirectory](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/CreatePromptPluginFromDirectory.cs)
- [CrewAI_Plugin](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/CrewAI_Plugin.cs)
- [OpenApiPlugin_PayloadHandling](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/OpenApiPlugin_PayloadHandling.cs)
- [OpenApiPlugin_CustomHttpContentReader](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/OpenApiPlugin_CustomHttpContentReader.cs)
- [OpenApiPlugin_Customization](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/OpenApiPlugin_Customization.cs)
- [OpenApiPlugin_Filtering](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/OpenApiPlugin_Filtering.cs)
- [OpenApiPlugin_Telemetry](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/OpenApiPlugin_Telemetry.cs)
- [OpenApiPlugin_RestApiOperationResponseFactory](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/OpenApiPlugin_RestApiOperationResponseFactory.cs)
- [CustomMutablePlugin](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/CustomMutablePlugin.cs)
- [DescribeAllPluginsAndFunctions](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/DescribeAllPluginsAndFunctions.cs)
- [GroundednessChecks](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/GroundednessChecks.cs)
- [ImportPluginFromGrpc](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/ImportPluginFromGrpc.cs)
- [TransformPlugin](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/TransformPlugin.cs)
- [CopilotAgentBasedPlugins](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/CopilotAgentBasedPlugins.cs)
- [WebPlaugins](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Plugins/WebPlugins.cs)

### PromptTemplates - 使用 [`Templates`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/PromptTemplate/IPromptTemplate.cs) 进行 `Prompt` 渲染的参数化

- [ChatCompletionPrompts](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/ChatCompletionPrompts.cs)
- [ChatLoopWithPrompt](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/ChatLoopWithPrompt.cs)
- [ChatPromptWithAudio](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/ChatPromptWithAudio.cs)
- [ChatPromptWithBinary](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/ChatPromptWithBinary.cs)
- [ChatWithPrompts](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/ChatWithPrompts.cs)
- [HandlebarsPrompts](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/HandlebarsPrompts.cs)
- [HandlebarsVisionPrompts](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/HandlebarsVisionPrompts.cs)
- [LiquidPrompts](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/LiquidPrompts.cs)
- [MultiplePromptTemplates](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/MultiplePromptTemplates.cs)
- [PromptFunctionsWithChatGPT](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/PromptFunctionsWithChatGPT.cs)
- [PromptyFunction](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/PromptyFunction.cs)
- [SafeChatPrompts](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/SafeChatPrompts.cs)
- [TemplateLanguage](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/PromptTemplates/TemplateLanguage.cs)

### RAG - 检索增强生成

- [WithFunctionCallingStepwisePlanner](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/RAG/WithFunctionCallingStepwisePlanner.cs)
- [WithPlugins](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/RAG/WithPlugins.cs)

### Search - 搜索服务信息

- [BingAndGooglePlugins](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Search/BingAndGooglePlugins.cs)
- [MyAzureAISearchPlugin](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Search/MyAzureAISearchPlugin.cs)
- [WebSearchQueriesPlugin](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Search/WebSearchQueriesPlugin.cs)

### TextGeneration - 使用 [`TextGeneration`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/TextGeneration/ITextGenerationService.cs) 服务的模型

- [Custom_TextGenerationService](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/TextGeneration/Custom_TextGenerationService.cs)
- [HuggingFace_TextGeneration](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/TextGeneration/HuggingFace_TextGeneration.cs)
- [OpenAI_TextGenerationStreaming](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/TextGeneration/OpenAI_TextGenerationStreaming.cs)

### TextToAudio - 使用 [`TextToAudio`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/TextToAudio/ITextToAudioService.cs) 服务生成音频

- [OpenAI_TextToAudio](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/TextToAudio/OpenAI_TextToAudio.cs)

### TextToImage - 使用 [`TextToImage`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/TextToImage/ITextToImageService.cs) 服务生成图像

- [OpenAI_TextToImage](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/TextToImage/OpenAI_TextToImage.cs)
- [OpenAI_TextToImageLegacy](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/TextToImage/OpenAI_TextToImageLegacy.cs)
- [AzureOpenAI_TextToImage](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/TextToImage/AzureOpenAI_TextToImage.cs)

## 配置

### 选项 1：使用 Secret Manager

概念示例需要秘密和凭据来访问 OpenAI、Azure OpenAI、Bing 和其他资源。

我们建议使用 .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) 来避免秘密泄露到存储库、分支和拉取请求中。如果您愿意，也可以使用环境变量。

使用 Secret Manager 设置您的秘密：

```
cd dotnet/src/samples/Concepts
dotnet user-secrets init
dotnet user-secrets set "OpenAI:ServiceId" "gpt-3.5-turbo-instruct"
dotnet user-secrets set "OpenAI:ModelId" "gpt-3.5-turbo-instruct"
dotnet user-secrets set "OpenAI:ChatModelId" "gpt-4"
dotnet user-secrets set "OpenAI:ApiKey" "..."
...
```

### 选项 2：使用配置文件

1. 在 `Concepts.csproj` 文件旁边创建一个 `appsettings.Development.json` 文件。此文件将被 git 忽略，其内容不会出现在拉取请求中，因此对于个人设置是安全的。请妥善保管此文件。
2. 编辑 `appsettings.Development.json` 并为您运行的示例设置适当的配置。

例如：

```json
{
  "OpenAI": {
    "ServiceId": "gpt-3.5-turbo-instruct",
    "ModelId": "gpt-3.5-turbo-instruct",
    "ChatModelId": "gpt-4",
    "ApiKey": "sk-...."
  },
  "AzureOpenAI": {
    "ServiceId": "azure-gpt-35-turbo-instruct",
    "DeploymentName": "gpt-35-turbo-instruct",
    "ChatDeploymentName": "gpt-4",
    "Endpoint": "https://contoso.openai.azure.com/",
    "ApiKey": "...."
  }
  // etc.
}
```

### 选项 3：使用环境变量

您还可以在环境变量中设置设置。环境变量将覆盖 `appsettings.Development.json` 文件中的设置。

设置环境变量时，使用双下划线（即 "\_\_"）来区分父属性和子属性。例如：

- bash:

```bash
  export OpenAI__ApiKey="sk-...."
  export AzureOpenAI__ApiKey="...."
  export AzureOpenAI__DeploymentName="gpt-35-turbo-instruct"
  export AzureOpenAI__ChatDeploymentName="gpt-4"
  export AzureOpenAIEmbeddings__DeploymentName="azure-text-embedding-ada-002"
  export AzureOpenAI__Endpoint="https://contoso.openai.azure.com/"
  export HuggingFace__ApiKey="...."
  export Bing__ApiKey="...."
  export Postgres__ConnectionString="...."
  ```

- PowerShell:

   ```ps
  $env:OpenAI__ApiKey = "sk-...."
  $env:AzureOpenAI__ApiKey = "...."
  $env:AzureOpenAI__DeploymentName = "gpt-35-turbo-instruct"
  $env:AzureOpenAI__ChatDeploymentName = "gpt-4"
  $env:AzureOpenAIEmbeddings__DeploymentName = "azure-text-embedding-ada-002"
  $env:AzureOpenAI__Endpoint = "https://contoso.openai.azure.com/"
  $env:HuggingFace__ApiKey = "...."
  $env:Bing__ApiKey = "...."
  $env:Postgres__ConnectionString = "...."
  ```
