// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

/// <summary>
/// Represents a client for token counting Gemini model.
/// </summary>
internal sealed class GeminiTokenCounterClient : ClientBase
{
    private readonly string _modelId;
    private readonly Uri _tokenCountingEndpoint;

    /// <summary>
    /// Represents a client for token counting Gemini via GoogleAI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model to use to counting tokens</param>
    /// <param name="apiKey">Api key for GoogleAI endpoint</param>
    /// <param name="apiVersion">Version of the Google API</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GeminiTokenCounterClient(
        HttpClient httpClient,
        string modelId,
        string apiKey,
        GoogleAIVersion apiVersion,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            logger: logger)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        string versionSubLink = GetApiVersionSubLink(apiVersion);

        this._modelId = modelId;
        this._tokenCountingEndpoint = new Uri($"https://generativelanguage.googleapis.com/{versionSubLink}/models/{this._modelId}:countTokens?key={apiKey}");
    }

    /// <summary>
    /// Represents a client for token counting Gemini via VertexAI.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model to use to counting tokens</param>
    /// <param name="bearerTokenProvider">Bearer key provider used for authentication</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Project ID from google cloud</param>
    /// <param name="apiVersion">Version of the Vertex API</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GeminiTokenCounterClient(
        HttpClient httpClient,
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        string location,
        string projectId,
        VertexAIVersion apiVersion,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            logger: logger,
            bearerTokenProvider: bearerTokenProvider)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(location);
        Verify.ValidHostnameSegment(location);
        Verify.NotNullOrWhiteSpace(projectId);

        string versionSubLink = GetApiVersionSubLink(apiVersion);

        this._modelId = modelId;
        this._tokenCountingEndpoint = new Uri($"https://{location}-aiplatform.googleapis.com/{versionSubLink}/projects/{projectId}/locations/{location}/publishers/google/models/{this._modelId}:countTokens");
    }

    /// <summary>
    /// Counts the number of tokens asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt to count tokens from.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>The number of tokens.</returns>
    public async Task<int> CountTokensAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var geminiRequest = CreateGeminiRequest(prompt, executionSettings);
        using var httpRequestMessage = await this.CreateHttpRequestAsync(geminiRequest, this._tokenCountingEndpoint).ConfigureAwait(false);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return DeserializeAndProcessCountTokensResponse(body);
    }

    private static int DeserializeAndProcessCountTokensResponse(string body)
    {
        var node = DeserializeResponse<JsonNode>(body);
        return node["totalTokens"]?.GetValue<int>() ?? throw new KernelException("Invalid response from model");
    }

    private static GeminiRequest CreateGeminiRequest(
        string prompt,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var geminiExecutionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(geminiExecutionSettings.MaxTokens);
        var geminiRequest = GeminiRequest.FromPromptAndExecutionSettings(prompt, geminiExecutionSettings);
        return geminiRequest;
    }
}
