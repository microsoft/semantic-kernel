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
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Gemini.Settings;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

/// <summary>
/// Represents a client for interacting with the Gemini API.
/// </summary>
internal sealed class GeminiClient
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

        var endpoint = GeminiEndpoints.GetTextGenerationEndpoint(this._model, this._apiKey);
        var geminiRequest = CreateGeminiRequestFromPrompt(prompt, executionSettings);
        using var httpRequestMessage = CreateHTTPRequestMessage(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return this.DeserializeAndProcessTextResponse(body);
    }

    /// <summary>
    /// Streams the generated text content asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt for generating text content.</param>
    /// <param name="executionSettings">The prompt execution settings (optional).</param>
    /// <param name="cancellationToken">The cancellation token (optional).</param>
    /// <returns>An asynchronous enumerable of <see cref="StreamingTextContent"/> streaming text contents.</returns>
    public async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);

        var endpoint = GeminiEndpoints.GetStreamTextGenerationEndpoint(this._model, this._apiKey);
        var geminiRequest = CreateGeminiRequestFromPrompt(prompt, executionSettings);
        using var httpRequestMessage = CreateHTTPRequestMessage(geminiRequest, endpoint);

        using var response = await this.SendRequestAndGetResponseStreamAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        await foreach (var streamingTextContent in this.ProcessTextResponseStreamAsync(responseStream, cancellationToken))
        {
            yield return streamingTextContent;
        }
    }

    public async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        ValidateChatHistory(chatHistory);
        var endpoint = GeminiEndpoints.GetChatCompletionEndpoint(this._model, this._apiKey);
        var geminiRequest = CreateGeminiRequestFromChatHistory(chatHistory, executionSettings);
        using var httpRequestMessage = CreateHTTPRequestMessage(geminiRequest, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        return this.DeserializeAndProcessChatResponse(body);
    }

    public async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ValidateChatHistory(chatHistory);
        var endpoint = GeminiEndpoints.GetStreamChatCompletionEndpoint(this._model, this._apiKey);
        var geminiRequest = CreateGeminiRequestFromChatHistory(chatHistory, executionSettings);
        using var httpRequestMessage = CreateHTTPRequestMessage(geminiRequest, endpoint);

        using var response = await this.SendRequestAndGetResponseStreamAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        await foreach (var streamingChatMessageContent in this.ProcessChatResponseStreamAsync(responseStream, cancellationToken))
        {
            yield return streamingChatMessageContent;
        }
    }

    #region PRIVATE METHODS

    private static void ValidateChatHistory(ChatHistory chatHistory)
    {
        if (chatHistory.Any(message => message.Role == AuthorRole.System))
        {
            // TODO: Temporary solution, maybe we can support system messages with two messages in the chat history (one from the user and one from the assistant)
            throw new NotSupportedException("Gemini API currently doesn't support system messages.");
        }
    }

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

    private async IAsyncEnumerable<StreamingTextContent> ProcessTextResponseStreamAsync(
        Stream responseStream,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        using var streamReader = new StreamReader(responseStream, Encoding.UTF8);
        var jsonStringBuilder = new StringBuilder();
        while (await streamReader.ReadLineAsync().ConfigureAwait(false) is { } line)
        {
            if (line is "," or "]")
            {
                foreach (var textContent in this.DeserializeAndProcessTextResponse(jsonStringBuilder.ToString()))
                {
                    yield return GetStreamingTextContentFromTextContent(textContent);
                }

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

    private async IAsyncEnumerable<StreamingChatMessageContent> ProcessChatResponseStreamAsync(
        Stream responseStream,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        using var streamReader = new StreamReader(responseStream, Encoding.UTF8);
        var jsonStringBuilder = new StringBuilder();
        while (await streamReader.ReadLineAsync().ConfigureAwait(false) is { } line)
        {
            if (line is "," or "]")
            {
                foreach (var chatMessageContent in this.DeserializeAndProcessChatResponse(jsonStringBuilder.ToString()))
                {
                    yield return GetStreamingChatContentFromChatContent(chatMessageContent);
                }

                jsonStringBuilder.Clear();
            }
            else
            {
                RemoveLeftBracketAndAppendJsonLine(line, jsonStringBuilder);
            }
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

    private List<TextContent> DeserializeAndProcessTextResponse(string body)
    {
        var geminiResponse = DeserializeGeminiResponse(body);
        return this.ProcessTextResponse(geminiResponse);
    }

    private List<ChatMessageContent> DeserializeAndProcessChatResponse(string body)
    {
        var geminiResponse = DeserializeGeminiResponse(body);
        return this.ProcessChatResponse(geminiResponse);
    }

    private static GeminiResponse DeserializeGeminiResponse(string body)
    {
        var geminiResponse = JsonSerializer.Deserialize<GeminiResponse>(body);
        if (geminiResponse is null)
        {
            throw new KernelException("Unexpected response from model")
            {
                Data = { { "ResponseData", body } },
            };
        }

        return geminiResponse;
    }

    private List<TextContent> ProcessTextResponse(GeminiResponse geminiResponse)
    {
        return geminiResponse.Candidates.Select(candidate => new TextContent(
            text: candidate.Content.Parts[0].Text,
            modelId: this._model,
            innerContent: candidate,
            metadata: GetResponseMetadata(geminiResponse, candidate))).ToList();
    }

    private List<ChatMessageContent> ProcessChatResponse(GeminiResponse geminiResponse)
    {
        return geminiResponse.Candidates.Select(candidate => new ChatMessageContent(
            role: GeminiChatRole.ToAuthorRole(candidate.Content.Role),
            content: candidate.Content.Parts[0].Text,
            modelId: this._model,
            innerContent: candidate,
            metadata: GetResponseMetadata(geminiResponse, candidate))).ToList();
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

    private static HttpRequestMessage CreateHTTPRequestMessage(
        GeminiRequest geminiRequest,
        Uri endpoint)
    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, geminiRequest);
        httpRequestMessage.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);
        return httpRequestMessage;
    }

    private static GeminiRequest CreateGeminiRequestFromPrompt(
        string prompt,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var geminiExecutionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        var geminiRequest = GeminiRequest.FromPromptAndExecutionSettings(prompt, geminiExecutionSettings);
        return geminiRequest;
    }

    private static GeminiRequest CreateGeminiRequestFromChatHistory(
        ChatHistory chatHistory,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var geminiExecutionSettings = GeminiPromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        var geminiRequest = GeminiRequest.FromChatHistoryAndExecutionSettings(chatHistory, geminiExecutionSettings);
        return geminiRequest;
    }

    private static StreamingTextContent GetStreamingTextContentFromTextContent(TextContent textContent)
        => new(
            text: textContent.Text,
            modelId: textContent.ModelId,
            innerContent: textContent.InnerContent,
            metadata: textContent.Metadata,
            choiceIndex: Convert.ToInt32(textContent.Metadata!["Index"], new NumberFormatInfo()));

    private static StreamingChatMessageContent GetStreamingChatContentFromChatContent(ChatMessageContent chatMessageContent)
        => new(
            role: chatMessageContent.Role,
            content: chatMessageContent.Content,
            modelId: chatMessageContent.ModelId,
            innerContent: chatMessageContent.InnerContent,
            metadata: chatMessageContent.Metadata,
            choiceIndex: Convert.ToInt32(chatMessageContent.Metadata!["Index"], new NumberFormatInfo()));

    #endregion
}
