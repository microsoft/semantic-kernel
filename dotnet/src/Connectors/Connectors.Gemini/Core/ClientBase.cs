#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Gemini.Abstract;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

internal abstract class ClientBase
{
    private readonly IStreamJsonParser _streamJsonParser;
    protected HttpClient HTTPClient { get; }
    protected string APIKey { get; }

    protected ClientBase(IStreamJsonParser streamJsonParser, HttpClient httpClient, string apiKey)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        this.HTTPClient = httpClient;
        this.APIKey = apiKey;
        this._streamJsonParser = streamJsonParser;
    }

    protected void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens is < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    protected async Task<string> SendRequestAndGetStringBodyAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        using var response = await this.HTTPClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var body = await response.Content.ReadAsStringWithExceptionMappingAsync()
            .ConfigureAwait(false);
        return body;
    }

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
    protected async IAsyncEnumerable<GeminiResponse> ProcessResponseStreamAsync(
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
        Stream responseStream,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        foreach (string json in this._streamJsonParser.Parse(responseStream))
        {
            yield return DeserializeResponse<GeminiResponse>(json);
        }
    }

    protected async Task<HttpResponseMessage> SendRequestAndGetResponseStreamAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        var response = await this.HTTPClient.SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
            .ConfigureAwait(false);
        return response;
    }

    protected static T DeserializeResponse<T>(string body)
    {
        T? geminiResponse = JsonSerializer.Deserialize<T>(body);
        if (geminiResponse is null)
        {
            throw new KernelException("Unexpected response from model")
            {
                Data = { { "ResponseData", body } },
            };
        }

        return geminiResponse;
    }

    protected static ReadOnlyDictionary<string, object?> GetResponseMetadata(
        GeminiResponse geminiResponse,
        GeminiResponseCandidate candidate) => new GeminiMetadata()
    {
        FinishReason = candidate.FinishReason,
        Index = candidate.Index,
        PromptTokenCount = geminiResponse.UsageMetadata?.PromptTokenCount ?? 0,
        CurrentCandidateTokenCount = candidate.TokenCount,
        CandidatesTokenCount = geminiResponse.UsageMetadata?.CandidatesTokenCount ?? 0,
        TotalTokenCount = geminiResponse.UsageMetadata?.TotalTokenCount ?? 0,
        PromptFeedbackBlockReason = geminiResponse.PromptFeedback?.BlockReason,
        PromptFeedbackSafetyRatings = geminiResponse.PromptFeedback?.SafetyRatings?.ToList(),
        ResponseSafetyRatings = candidate.SafetyRatings?.ToList(),
    };

    protected static HttpRequestMessage CreateHTTPRequestMessage(
        object requestData,
        Uri endpoint)
    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, requestData);
        httpRequestMessage.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);
        return httpRequestMessage;
    }
}
