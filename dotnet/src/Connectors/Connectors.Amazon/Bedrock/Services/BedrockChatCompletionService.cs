// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Services;

/// <summary>
/// Represents a chat completion service using Amazon Bedrock API.
/// </summary>
public class BedrockChatCompletionService : IChatCompletionService
{
    private readonly Dictionary<string, object?> _attributesInternal = [];
    private readonly BedrockChatCompletionClient _chatCompletionClient;

    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService using an IAmazonBedrockRuntime object passed in by the user.
    /// </summary>
    /// <param name="modelId">The model to be used for chat completion.</param>
    /// <param name="bedrockApi">The IAmazonBedrockRuntime object to be used for DI.</param>
    /// <param name="loggerFactory">Logger.</param>
    public BedrockChatCompletionService(string modelId, IAmazonBedrockRuntime bedrockApi, ILoggerFactory? loggerFactory = null)
    {
        this._chatCompletionClient = new BedrockChatCompletionClient(modelId, bedrockApi, loggerFactory);
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
        return this._chatCompletionClient.GenerateChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._chatCompletionClient.StreamChatMessageAsync(chatHistory, executionSettings, kernel, cancellationToken);
    }
}
