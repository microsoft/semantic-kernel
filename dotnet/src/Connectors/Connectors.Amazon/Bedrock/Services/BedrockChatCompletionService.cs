// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.Runtime;
using Connectors.Amazon.Core;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

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
    /// <param name="modelId"></param>
    /// <param name="bedrockApi"></param>
    public BedrockChatCompletionService(string modelId, IAmazonBedrockRuntime bedrockApi)
        : base(modelId, bedrockApi)
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService by creating a new AmazonBedrockRuntimeClient().
    /// </summary>
    /// <param name="modelId"></param>
    public BedrockChatCompletionService(string modelId)
        : base(modelId, new AmazonBedrockRuntimeClient())
    {
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }
    /// <summary>
    /// Initializes an instance of the BedrockChatCompletionService with AWSCredentials object for authentication.
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="awsCredentials"></param>
    public BedrockChatCompletionService(string modelId, AWSCredentials awsCredentials)
        : base(modelId, new AmazonBedrockRuntimeClient(awsCredentials))
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
