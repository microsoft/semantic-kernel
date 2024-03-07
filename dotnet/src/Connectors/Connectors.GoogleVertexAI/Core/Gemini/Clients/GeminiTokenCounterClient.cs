// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core;

/// <summary>
/// Represents a client for token counting gemini model.
/// </summary>
internal sealed class GeminiTokenCounterClient : ClientBase
{
    private readonly string _modelId;
    private readonly Uri _tokenCountingEndpoint;

    /// <summary>
    /// Represents a client for token counting gemini model.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model to use to counting tokens</param>
    /// <param name="httpRequestFactory">Request factory for gemini rest api or gemini vertex ai</param>
    /// <param name="tokenCountingEndpoint">The endpoint for token counting</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public GeminiTokenCounterClient(
        HttpClient httpClient,
        string modelId,
        IHttpRequestFactory httpRequestFactory,
        Uri tokenCountingEndpoint,
        ILogger? logger = null)
        : base(
            httpClient: httpClient,
            httpRequestFactory: httpRequestFactory,
            logger: logger)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(tokenCountingEndpoint);

        this._modelId = modelId;
        this._tokenCountingEndpoint = tokenCountingEndpoint;
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
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(geminiRequest, this._tokenCountingEndpoint);

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
