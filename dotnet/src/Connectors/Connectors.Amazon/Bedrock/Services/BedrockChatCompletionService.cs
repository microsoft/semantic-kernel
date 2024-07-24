// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Services;

/// <summary>
/// Represents a chat completion service using Amazon Bedrock API.
/// </summary>
public class BedrockChatCompletionService : BedrockChatCompletionClient<IChatCompletionRequest, IChatCompletionResponse>, IChatCompletionService
{
    private readonly Dictionary<string, object?> _attributesInternal = [];

    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService using an IAmazonBedrockRuntime object passed in by the user.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="bedrockApi">The IAmazonBedrockRuntime object to be used for DI.</param>
    public BedrockChatCompletionService(string modelId, IAmazonBedrockRuntime bedrockApi)
        : base(modelId, bedrockApi)
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

    /// <inheritdoc />
    public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.GenerateChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.StreamChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }
}
