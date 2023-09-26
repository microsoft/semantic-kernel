// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/// <summary>
/// Azure OpenAI chat completion client.
/// TODO: forward ETW logging to ILogger, see https://learn.microsoft.com/en-us/dotnet/azure/sdk/logging
/// </summary>
public sealed class AzureChatCompletion : AzureOpenAIClientBase, IChatStreamingCompletion, ITextStreamingCompletion
{
    /// <summary>
    /// Create an instance of the Azure OpenAI chat completion connector with API key auth
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureChatCompletion(
        string modelId,
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null) : base(modelId, endpoint, apiKey, httpClient, loggerFactory)
    {
    }

    /// <summary>
    /// Create an instance of the Azure OpenAI chat completion connector with AAD auth
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureChatCompletion(
        string modelId,
        string endpoint,
        TokenCredential credentials,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null) : base(modelId, endpoint, credentials, httpClient, loggerFactory)
    {
    }

    /// <summary>
    /// Creates a new AzureChatCompletion client instance using the specified OpenAIClient
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureChatCompletion(
        string modelId,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null) : base(modelId, openAIClient, loggerFactory)
    {
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<IChatResult>> GetChatResultsAsync(
        ChatHistory chat,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetChatResultsAsync(chat, requestSettings, cancellationToken);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<IChatStreamingResult> GetChatStreamingResultsAsync(
        ChatHistory chat,
        AIRequestSettings? requestSettings = null,
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
    public IAsyncEnumerable<ITextStreamingResult> GetTextStreamingResultsAsync(
        string text,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetChatStreamingResultsAsTextAsync(text, requestSettings, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<ITextResult>> GetTextResultsAsync(
        string text,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetChatResultsAsTextAsync(text, requestSettings, cancellationToken);
    }
}
