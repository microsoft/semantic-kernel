#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
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
        Verify.NotNullOrWhiteSpace(prompt);

        var endpoint = GeminiEndpoints.GetGenerateContentEndpoint(this._model, this._apiKey);
        using var httpRequestMessage = GetHTTPRequestMessage(prompt, executionSettings, endpoint);

        using var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var body = await response.Content.ReadAsStringWithExceptionMappingAsync()
            .ConfigureAwait(false);

        return this.DeserializeAndProcessResponseBody(body);
    }

    private List<TextContent> DeserializeAndProcessResponseBody(string body)
    {
        var geminiResponse = JsonSerializer.Deserialize<GeminiResponse>(body);
        if (geminiResponse is null)
        {
            throw new KernelException("Unexpected response from model")
            {
                Data = { { "ResponseData", body } },
            };
        }

        return geminiResponse.Candidates.Select(c => new TextContent(c.Content.Parts[0].Text,
            this.GetModelId(), innerContent: c, metadata: GetResponseMetadata(geminiResponse, c))).ToList();
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

    private static HttpRequestMessage GetHTTPRequestMessage(
        string prompt,
        PromptExecutionSettings? promptExecutionSettings,
        Uri endpoint)
    {
        var geminiExecutionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        var geminiRequest = GeminiRequest.FromPromptExecutionSettings(prompt, geminiExecutionSettings);
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, geminiRequest);
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
        return this.InternalGetStreamingTextContentsAsync(prompt, executionSettings, cancellationToken);
    }

    private async IAsyncEnumerable<StreamingTextContent> InternalGetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var endpoint = GeminiEndpoints.GetStreamGenerateContentEndpoint(this._model, this._apiKey);
        using var httpRequestMessage = GetHTTPRequestMessage(prompt, executionSettings, endpoint);

        using var response = await this._httpClient
            .SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
            .ConfigureAwait(false);
        var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        using var streamReader = new StreamReader(responseStream, Encoding.UTF8);
        var jsonStringBuilder = new StringBuilder();
        while (await streamReader.ReadLineAsync().ConfigureAwait(false) is { } line)
        {
            if (line is "," or "]")
            {
                string json = jsonStringBuilder.ToString();
                foreach (var textContent in this.DeserializeAndProcessResponseBody(json))
                {
                    yield return GetStreamingTextContentFromTextContent(textContent);
                }

                jsonStringBuilder = new StringBuilder();
                continue;
            }

            if (line[0] == '[')
            {
                line = line.Length > 1 ? line.Substring(1) : "";
            }

            jsonStringBuilder.Append(line);
        }
    }

    private static StreamingTextContent GetStreamingTextContentFromTextContent(TextContent textContent)
    {
        return new StreamingTextContent(
            text: textContent.Text,
            modelId: textContent.ModelId,
            innerContent: textContent.InnerContent,
            metadata: textContent.Metadata,
            choiceIndex: Convert.ToInt32(textContent.Metadata!["Index"], new NumberFormatInfo()));
    }
}
