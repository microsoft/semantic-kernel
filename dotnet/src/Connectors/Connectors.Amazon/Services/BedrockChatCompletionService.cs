// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Connectors.Amazon.Core;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;

namespace Connectors.Amazon.Services;

public class BedrockChatCompletionService : BedrockClientBase<IChatCompletionRequest, IChatCompletionResponse>, IChatCompletionService
{
    private readonly AmazonBedrockRuntimeClient _chatCompletionClient;
    public BedrockChatCompletionService(string modelId, IAmazonBedrockRuntime bedrockApi, IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse> ioService)
        : base(modelId, bedrockApi, ioService)
    {
    }

    public BedrockChatCompletionService(string modelId, IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse> ioService)
        : base(modelId, new AmazonBedrockRuntimeClient(), ioService)
    {
    }

    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return GenerateChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }

    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }
}
