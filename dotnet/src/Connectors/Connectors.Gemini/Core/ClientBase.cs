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
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

internal abstract class ClientBase
{
    protected HttpClient HTTPClient { get; }
    protected string APIKey { get; }

    protected ClientBase(HttpClient httpClient, string apiKey)
    {
        Verify.NotNullOrWhiteSpace(apiKey);

        this.HTTPClient = httpClient;
        this.APIKey = apiKey;
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

    protected static async IAsyncEnumerable<GeminiResponse> ProcessResponseStreamAsync(
        Stream responseStream,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        using var streamReader = new StreamReader(responseStream, Encoding.UTF8);
        var jsonStringBuilder = new StringBuilder();
        while (await streamReader.ReadLineAsync().ConfigureAwait(false) is { } line)
        {
            if (line is "," or "]")
            {
                yield return DeserializeResponse<GeminiResponse>(jsonStringBuilder.ToString());
                jsonStringBuilder.Clear();
            }
            else
            {
                RemoveLeftBracketAndAppendJsonLine(line, jsonStringBuilder);
            }
        }
    }

    private static void RemoveLeftBracketAndAppendJsonLine(string line, StringBuilder jsonStringBuilder)
    {
        if (line[0] == '[')
        {
            line = line.Length > 1 ? line.Substring(1) : "";
        }

        jsonStringBuilder.Append(line);
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
