// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Models;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;

/// <summary>
/// OpenAI text completion service.
/// TODO: forward ETW logging to ILogger, see https://learn.microsoft.com/en-us/dotnet/azure/sdk/logging
/// </summary>
public sealed class OpenAITextCompletion : OpenAIClientBase, ITextCompletion
{
    /// <summary>
    /// Create an instance of the OpenAI text completion connector
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    public OpenAITextCompletion(
        string modelId,
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILogger? logger = null
    ) : base(modelId, apiKey, organization, httpClient, logger)
    {
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<ITextCompletionStreamingResult> GetStreamingCompletionsAsync(
        string text,
        JsonObject requestSettings,
        CancellationToken cancellationToken = default)
    {
        return this.InternalGetTextStreamingResultsAsync(text, requestSettings, cancellationToken);
        var settings = CompletionRequestSettings.FromJson(requestSettings);
        return this.InternalCompleteTextAsync(text, settings, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<IReadOnlyList<ITextCompletionResult>> GetCompletionsAsync(
        string text,
        JsonObject requestSettings,
        CancellationToken cancellationToken = default)
    {
        return this.InternalGetTextResultsAsync(text, requestSettings, cancellationToken);
        var settings = CompletionRequestSettings.FromJson(requestSettings);
        return this.InternalCompletionStreamAsync(text, settings, cancellationToken);
    }
}
