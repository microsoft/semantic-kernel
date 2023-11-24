// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;

/// <summary>
/// Azure OpenAI text completion client.
/// TODO: forward ETW logging to ILogger, see https://learn.microsoft.com/en-us/dotnet/azure/sdk/logging
/// </summary>
public sealed class AzureTextCompletion : AzureOpenAIClientBase, ITextCompletion
{
    /// <inheritdoc/>
    public IReadOnlyDictionary<string, string> Attributes => this.InternalAttributes;

    /// <summary>
    /// Creates a new AzureTextCompletion client instance using API Key auth
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureTextCompletion(
        string deploymentName,
        string endpoint,
        string apiKey,
        string? modelId = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null) : base(deploymentName, endpoint, apiKey, httpClient, loggerFactory)
    {
        this.AddAttribute(IAIServiceExtensions.ModelIdKey, modelId);
    }

    /// <summary>
    /// Creates a new AzureTextCompletion client instance supporting AAD auth
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureTextCompletion(
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? modelId = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null) : base(deploymentName, endpoint, credential, httpClient, loggerFactory)
    {
        this.AddAttribute(IAIServiceExtensions.ModelIdKey, modelId);
    }

    /// <summary>
    /// Creates a new AzureTextCompletion client instance using the specified OpenAIClient
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureTextCompletion(
        string deploymentName,
        OpenAIClient openAIClient,
        string? modelId = null,
        ILoggerFactory? loggerFactory = null) : base(deploymentName, openAIClient, loggerFactory)
    {
        this.AddAttribute(IAIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(
        string text,
        AIRequestSettings? requestSettings,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetTextStreamingResultsAsync(text, requestSettings, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string text,
        AIRequestSettings? requestSettings,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetTextResultsAsync(text, requestSettings, cancellationToken);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<T> GetStreamingContentAsync<T>(string prompt, AIRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        return this.InternalGetTextStreamingUpdatesAsync<T>(prompt, requestSettings, cancellationToken);
    }
}
