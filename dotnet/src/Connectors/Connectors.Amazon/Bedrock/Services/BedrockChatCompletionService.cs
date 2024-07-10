// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Connectors.Amazon.Core;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.TextGeneration;

namespace Connectors.Amazon.Services;

public class BedrockChatCompletionService : BedrockChatCompletionClient<IChatCompletionRequest, IChatCompletionResponse>, IChatCompletionService
{
    private readonly Dictionary<string, object?> _attributesInternal = [];
    private readonly BedrockChatCompletionClient<IChatCompletionRequest, IChatCompletionResponse> _chatCompletionClient;
    public BedrockChatCompletionService(string modelId, IAmazonBedrockRuntime bedrockApi)
        : base(modelId, bedrockApi)
    {
    }
    public BedrockChatCompletionService(string modelId)
        : base(modelId, new AmazonBedrockRuntimeClient())
    {
    }
    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

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
        return StreamChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }
}
