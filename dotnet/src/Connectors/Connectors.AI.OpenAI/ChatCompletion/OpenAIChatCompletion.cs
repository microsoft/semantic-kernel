// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using AzureSdk;
using Extensions.Logging;
using SemanticKernel.AI.ChatCompletion;
using SemanticKernel.AI.TextCompletion;


/// <summary>
/// OpenAI chat completion client.
/// TODO: forward ETW logging to ILogger, see https://learn.microsoft.com/en-us/dotnet/azure/sdk/logging
/// </summary>
public sealed class OpenAIChatCompletion : OpenAIClientBase
{
    /// <summary>
    /// Create an instance of the OpenAI chat completion connector
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIChatCompletion(
        string modelId,
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null) : base(modelId, apiKey, organization, httpClient, loggerFactory)
    {
    }


    /// <summary>
    /// Create an instance of the OpenAI chat completion connector
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAIChatCompletion(
        string modelId,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null) : base(modelId, openAIClient, loggerFactory)
    {
    }


    /// <inheritdoc/>
    public Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        LogActionDetails();
        return InternalGetChatResultsAsync(chat, requestSettings, cancellationToken);
    }


    /// <inheritdoc/>
    public IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        LogActionDetails();
        return InternalGetChatStreamingResultsAsync(chat, requestSettings, cancellationToken);
    }


    /// <inheritdoc/>
    public ChatHistory CreateNewChat(string? instructions = null) => InternalCreateNewChat(instructions);


    /// <inheritdoc/>
    public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(
        string text,
        CompleteRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        LogActionDetails();
        return InternalGetChatStreamingResultsAsTextAsync(text, requestSettings, cancellationToken);
    }


    /// <inheritdoc/>
    public Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string text,
        CompleteRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        LogActionDetails();
        return InternalGetChatResultsAsTextAsync(text, requestSettings, cancellationToken);
    }
}
