#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Gemini.Settings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.Gemini;

/// <summary>
/// Represents a service for generating text using the Gemini API.
/// </summary>
public sealed class GeminiTextGenerationService : ITextGenerationService
{
    private readonly Dictionary<string, object?> _attributes = new();
    private readonly string _model;
    private readonly HttpClient _httpClient;
    private readonly string _apiKey;

    /// <summary>
    /// Initializes a new instance of the <see cref="GeminiTextGenerationService"/> class.
    /// </summary>
    /// <param name="model">The model identifier.</param>
    /// <param name="apiKey">The API key.</param>
    /// <param name="httpClient">The optional HTTP client.</param>
    public GeminiTextGenerationService(string model, string apiKey, HttpClient? httpClient = null)
    {
        Verify.NotNullOrWhiteSpace(model);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._model = model;
        this._apiKey = apiKey;
        this._httpClient = HttpClientProvider.GetHttpClient(httpClient);
        this._attributes.Add(AIServiceExtensions.ModelIdKey, this._model);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <inheritdoc />
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.InternalGetTextContentsAsync(prompt, executionSettings, cancellationToken);
    }

    private async Task<IReadOnlyList<TextContent>> InternalGetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken)
    {
        using var httpRequestMessage = this.VerifyArgumentsAndGetHTTPRequestMessage(prompt, executionSettings);

        using var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
        var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        var geminiResponse = JsonSerializer.Deserialize<GeminiResponse>(body);
        if (geminiResponse is null)
        {
            throw new KernelException("Unexpected response from model")
            {
                Data = { { "ResponseData", body } },
            };
        }

        return geminiResponse.Candidates.Select(c => new TextContent(c.Content.Parts[0].Text,
            this.GetModelId(), geminiResponse, metadata: GetResponseMetadata(geminiResponse, c))).ToList();
    }

    private static Dictionary<string, object?> GetResponseMetadata(
        GeminiResponse geminiResponse,
        GeminiResponseCandidate candidate) => new()
    {
        ["FinishReason"] = candidate.FinishReason,
        ["Index"] = candidate.Index,
        ["TokenCount"] = candidate.TokenCount,
        ["SafetyRatings"] = candidate.SafetyRatings?.Select(sr => new Dictionary<string, object?>
        {
            ["Block"] = sr.Block,
            ["Category"] = sr.Category,
            ["Probability"] = sr.Probability,
        } as IReadOnlyDictionary<string, object?>),
        ["PromptFeedbackBlockReason"] = geminiResponse.PromptFeedback?.BlockReason,
        ["PromptFeedbackSafetyRatings"] = geminiResponse.PromptFeedback?.SafetyRatings?.Select(sr => new Dictionary<string, object?>
        {
            ["Block"] = sr.Block,
            ["Category"] = sr.Category,
            ["Probability"] = sr.Probability,
        } as IReadOnlyDictionary<string, object?>),
    };

    private HttpRequestMessage VerifyArgumentsAndGetHTTPRequestMessage(string prompt, PromptExecutionSettings? executionSettings)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var geminiExecutionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(executionSettings);
        var httpRequestMessage = this.GetHTTPRequestMessage(prompt, geminiExecutionSettings);
        return httpRequestMessage;
    }

    private HttpRequestMessage GetHTTPRequestMessage(string prompt, GeminiPromptExecutionSettings geminiExecutionSettings)
    {
        var geminiRequest = GeminiRequest.FromPromptExecutionSettings(prompt, geminiExecutionSettings);
        var uri = GeminiEndpoints.GetGenerateContentEndpoint(this._model, this._apiKey);
        var httpRequestMessage = HttpRequest.CreatePostRequest(uri, geminiRequest);
        httpRequestMessage.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);
        return httpRequestMessage;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        // todo: implement streaming
        throw new NotImplementedException();
    }
}
