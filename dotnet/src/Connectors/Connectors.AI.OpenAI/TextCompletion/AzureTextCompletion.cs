// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;

/// <summary>
/// Azure OpenAI text completion client.
/// TODO: forward ETW logging to ILogger, see https://learn.microsoft.com/en-us/dotnet/azure/sdk/logging
/// </summary>
public sealed class AzureTextCompletion : AzureOpenAIClientBase, ITextCompletion
{
    /// <summary>
    /// Creates a new AzureTextCompletion client instance using API Key auth
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureTextCompletion(
        string modelId,
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null) : base(modelId, endpoint, apiKey, httpClient, loggerFactory)
    {
    }

    /// <summary>
    /// Creates a new AzureTextCompletion client instance supporting AAD auth
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureTextCompletion(
        string modelId,
        string endpoint,
        TokenCredential credential,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null) : base(modelId, endpoint, credential, httpClient, loggerFactory)
    {
    }

    /// <summary>
    /// Creates a new AzureTextCompletion client instance using the specified OpenAIClient
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureTextCompletion(
        string modelId,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null) : base(modelId, openAIClient, loggerFactory)
    {
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(
        string text,
        object? requestSettings,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetTextStreamingResultsAsync(text, requestSettings, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string text,
        object? requestSettings,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetTextResultsAsync(text, requestSettings, cancellationToken);
    }
}
