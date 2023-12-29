#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
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

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

/// <summary>
/// Represents a client for interacting with the Gemini API.
/// </summary>
internal class GeminiClient
{
    private readonly string _apiKey;
    private readonly HttpClient _httpClient;
    private readonly string _model;

    /// <summary>
    /// Initializes a new instance of the GeminiClient class.
    /// </summary>
    /// <param name="modelId">The ID of the model.</param>
    /// <param name="apiKey">The API key for authentication.</param>
    /// <param name="httpClient">The HttpClient instance to use for making HTTP requests.</param>
    public GeminiClient(string modelId, string apiKey, HttpClient httpClient)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._model = modelId;
        this._apiKey = apiKey;
        this._httpClient = httpClient;
    }

    /// <summary>
    /// Generates text based on the given prompt asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt for generating text content.</param>
    /// <param name="executionSettings">The prompt execution settings (optional).</param>
    /// <param name="cancellationToken">The cancellation token (optional).</param>
    /// <returns>A list of text content generated based on the prompt.</returns>
    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var endpoint = GeminiEndpoints.GetGenerateContentEndpoint(this._model, this._apiKey);
        using var httpRequestMessage = GetHTTPRequestMessage(prompt, executionSettings, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return this.DeserializeAndProcessResponseBody(body);
    }

    /// <summary>
    /// Streams the generated text content asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt for generating text content.</param>
    /// <param name="executionSettings">The prompt execution settings (optional).</param>
    /// <param name="cancellationToken">The cancellation token (optional).</param>
    /// <returns>An asynchronous enumerable of <see cref="StreamingTextContent"/> streaming text contents.</returns>
    public async IAsyncEnumerable<StreamingTextContent> StreamTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var endpoint = GeminiEndpoints.GetStreamGenerateContentEndpoint(this._model, this._apiKey);
        using var httpRequestMessage = GetHTTPRequestMessage(prompt, executionSettings, endpoint);

        using var response = await this.SendRequestAndGetResponseStreamAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        await foreach (var streamingTextContent in this.ProcessResponseStreamAsync(responseStream, cancellationToken))
        {
            yield return streamingTextContent;
        }
    }

    #region PRIVATE METHODS

    private async Task<string> SendRequestAndGetStringBodyAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        using var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var body = await response.Content.ReadAsStringWithExceptionMappingAsync()
            .ConfigureAwait(false);
        return body;
    }

    private async IAsyncEnumerable<StreamingTextContent> ProcessResponseStreamAsync(
        Stream responseStream,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        using var streamReader = new StreamReader(responseStream, Encoding.UTF8);
        var jsonStringBuilder = new StringBuilder();
        while (await streamReader.ReadLineAsync().ConfigureAwait(false) is { } line)
        {
            if (line is "," or "]")
            {
                foreach (var textContent in this.DeserializeAndProcessResponseBody(jsonStringBuilder.ToString()))
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

    private async Task<HttpResponseMessage> SendRequestAndGetResponseStreamAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        var response = await this._httpClient
            .SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
            .ConfigureAwait(false);
        return response;
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
            this._model, innerContent: c, metadata: GetResponseMetadata(geminiResponse, c))).ToList();
    }

    private static ReadOnlyDictionary<string, object?> GetResponseMetadata(
        GeminiResponse geminiResponse,
        GeminiResponseCandidate candidate) => new(new Dictionary<string, object?>
    {
        ["FinishReason"] = candidate.FinishReason,
        ["Index"] = candidate.Index,
        ["TokenCount"] = candidate.TokenCount,
        ["SafetyRatings"] = candidate.SafetyRatings?.Select(sr =>
            new ReadOnlyDictionary<string, object?>(new Dictionary<string, object?>
            {
                ["Block"] = sr.Block,
                ["Category"] = sr.Category,
                ["Probability"] = sr.Probability,
            })),
        ["PromptFeedbackBlockReason"] = geminiResponse.PromptFeedback?.BlockReason,
        ["PromptFeedbackSafetyRatings"] = geminiResponse.PromptFeedback?.SafetyRatings?.Select(sr =>
            new ReadOnlyDictionary<string, object?>(new Dictionary<string, object?>
            {
                ["Block"] = sr.Block,
                ["Category"] = sr.Category,
                ["Probability"] = sr.Probability,
            })),
    });

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

    private static StreamingTextContent GetStreamingTextContentFromTextContent(TextContent textContent)
    {
        return new StreamingTextContent(
            text: textContent.Text,
            modelId: textContent.ModelId,
            innerContent: textContent.InnerContent,
            metadata: textContent.Metadata,
            choiceIndex: Convert.ToInt32(textContent.Metadata!["Index"], new NumberFormatInfo()));
    }

    #endregion
}
