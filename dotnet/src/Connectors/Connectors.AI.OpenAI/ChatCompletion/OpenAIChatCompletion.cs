// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/// <summary>
/// OpenAI chat completion client.
/// TODO: forward ETW logging to ILogger, see https://learn.microsoft.com/en-us/dotnet/azure/sdk/logging
/// </summary>
public sealed class OpenAIChatCompletion : OpenAIClientBase, IChatCompletion, ITextCompletion
{
    /// <summary>
    /// Create an instance of the OpenAI chat completion connector
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    public OpenAIChatCompletion(
        string modelId,
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILogger? logger = null
    ) : base(modelId, apiKey, organization, httpClient, logger)
    {
    }

    /// <summary>
    /// Create an instance of the OpenAI chat completion connector
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    public OpenAIChatCompletion(
    string modelId,
    OpenAIClient openAIClient,
    ILogger? logger = null
) : base(modelId, openAIClient, logger)
    {
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetChatResultsAsync(chat, requestSettings, cancellationToken);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetChatStreamingResultsAsync(chat, requestSettings, cancellationToken);
    }

    /// <inheritdoc/>
    public ChatHistory CreateNewChat(string? instructions = null)
    {
        return InternalCreateNewChat(instructions);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(
        string text,
        CompleteRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetChatStreamingResultsAsTextAsync(text, requestSettings, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string text,
        CompleteRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetChatResultsAsTextAsync(text, requestSettings, cancellationToken);
    }
}
