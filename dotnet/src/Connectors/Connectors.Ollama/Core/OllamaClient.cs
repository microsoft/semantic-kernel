// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

internal sealed class OllamaClient : IOllamaClient
{
    private readonly IStreamJsonParser _streamJsonParser;
    private readonly string _modelId;

    private IHttpRequestFactory HttpRequestFactory { get; }
    private IEndpointProvider EndpointProvider { get; }
    private HttpClient HttpClient { get; }
    private ILogger Logger { get; }

    internal OllamaClient(
        string modelId,
        HttpClient httpClient,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        IStreamJsonParser? streamJsonParser = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);

        this._modelId = modelId;
        this.HttpClient = httpClient;
        this.HttpRequestFactory = httpRequestFactory;
        this.EndpointProvider = endpointProvider;
        this.Logger = logger ?? NullLogger.Instance;
        this._streamJsonParser = streamJsonParser ?? new OllamaStreamJsonParser();
    }

    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(string prompt, PromptExecutionSettings? executionSettings, CancellationToken cancellationToken)
    {
        var endpoint = this.EndpointProvider.TextGenerationEndpoint;
        var request = this.CreateTextRequest(prompt, executionSettings);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(request, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<OllamaTextResponse>(body);
        var textContents = GetTextContentFromResponse(response);

        this.LogUsage(textContents[0].Metadata! as OllamaMetadata);

        return textContents;
    }

    public async IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var endpoint = this.EndpointProvider.StreamTextGenerationEndpoint;
        var request = this.CreateTextRequest(prompt, executionSettings);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(request, endpoint);

        using var response = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        foreach (var streamingTextContent in this.ProcessTextResponseStream(responseStream))
        {
            yield return streamingTextContent;
        }
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        var endpoint = this.EndpointProvider.ChatCompletionEndpoint;
        var request = this.CreateChatRequest(chatHistory, executionSettings);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(request, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = DeserializeResponse<OllamaChatResponse>(body);

        var chatMessages = this.GetChatMessageContentsFromResponse(response);
        this.LogUsage(chatMessages[0].Metadata! as OllamaMetadata);

        return chatMessages;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var endpoint = this.EndpointProvider.StreamChatCompletionEndpoint;
        var request = this.CreateChatRequest(chatHistory, executionSettings);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(request, endpoint);

        using var response = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        foreach (var streamingChatMessageContent in this.ProcessChatResponseStream(responseStream))
        {
            yield return streamingChatMessageContent;
        }
    }

    private static void ValidateMaxTokens(int? maxTokens)
    {
        if (maxTokens is < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
        }
    }

    private async Task<string> SendRequestAndGetStringBodyAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        using var response = await this.HttpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var body = await response.Content.ReadAsStringWithExceptionMappingAsync()
            .ConfigureAwait(false);
        return body;
    }

    private async Task<HttpResponseMessage> SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        var response = await this.HttpClient.SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
            .ConfigureAwait(false);
        return response;
    }

    private IEnumerable<StreamingChatMessageContent> ProcessChatResponseStream(Stream stream)
        => from ollamaResponse in this.ParseChatResponseStream(stream)
           from chatMessageContent in this.GetChatMessageContentsFromResponse(ollamaResponse)
           select GetStreamingChatContentFromChatContent(chatMessageContent);

    private IEnumerable<StreamingTextContent> ProcessTextResponseStream(Stream stream)
        => from ollamaResponse in this.ParseTextResponseStream(stream)
           from textContent in this.GetTextContentsFromResponse(ollamaResponse)
           select GetStreamingTextContentFromTextContent(textContent);

    private IEnumerable<OllamaTextResponse> ParseTextResponseStream(Stream responseStream)
        => this._streamJsonParser.Parse(responseStream).Select(DeserializeResponse<OllamaTextResponse>);

    private IEnumerable<OllamaChatResponse> ParseChatResponseStream(Stream responseStream)
        => this._streamJsonParser.Parse(responseStream).Select(DeserializeResponse<OllamaChatResponse>);

    private List<ChatMessageContent> GetChatMessageContentsFromResponse(OllamaChatResponse response)
    {
        return new List<ChatMessageContent>
        {
            new(
                role: response.Message?.Role is null ? AuthorRole.Assistant : new AuthorRole(response.Message.Role),
                content: response.Message?.Content ?? string.Empty,
                modelId: this._modelId,
                innerContent: response,
                metadata: new OllamaMetadata(response))
        };
    }

    private List<TextContent> GetTextContentsFromResponse(OllamaTextResponse response)
    {
        return new List<TextContent>
        {
            new(text: response.Response,
                modelId: this._modelId,
                innerContent: response,
                metadata: new OllamaMetadata(response))
        };
    }
    private static StreamingChatMessageContent GetStreamingChatContentFromChatContent(ChatMessageContent chatMessageContent)
        => new(
            role: chatMessageContent.Role,
            content: chatMessageContent.Content,
            modelId: chatMessageContent.ModelId,
            innerContent: chatMessageContent.InnerContent,
            metadata: chatMessageContent.Metadata);

    private static StreamingTextContent GetStreamingTextContentFromTextContent(TextContent textContent)
        => new(
            text: textContent.Text,
            modelId: textContent.ModelId,
            innerContent: textContent.InnerContent,
            metadata: textContent.Metadata);

    private OllamaChatRequest CreateChatRequest(
        ChatHistory chatHistory,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(ollamaExecutionSettings.MaxTokens);
        var request = OllamaChatRequest.FromPromptAndExecutionSettings(chatHistory, ollamaExecutionSettings, this._modelId);
        return request;
    }

    private OllamaTextRequest CreateTextRequest(
        string prompt,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(ollamaExecutionSettings.MaxTokens);
        var request = OllamaTextRequest.FromPromptAndExecutionSettings(prompt, ollamaExecutionSettings, this._modelId);
        return request;
    }

    private static T DeserializeResponse<T>(string body)
    {
        try
        {
            T? deserializedResponse = JsonSerializer.Deserialize<T>(body);
            if (deserializedResponse is null)
            {
                throw new JsonException("Response is null");
            }

            return deserializedResponse;
        }
        catch (JsonException exc)
        {
            throw new KernelException("Unexpected response from model", exc)
            {
                Data = { { "ResponseData", body } },
            };
        }
    }

    private static List<TextContent> GetTextContentFromResponse(OllamaTextResponse response)
        => new()
        {
            new(response.Response, response.Model, response, Encoding.UTF8, new OllamaMetadata(response))
        };

    private void LogUsage(OllamaMetadata? metadata)
    {
        if (metadata is null)
        {
            return;
        }

        this.Logger.LogDebug(
            "Ollama usage metadata: Created At: {CreatedAt}, Eval Count: {EvalCount}, Eval Duration: {EvalDuration}, Total Duration: {TotalDuration}, Load Duration: {LoadDuration}, Prompt Eval Count: {PromptEvalCount}, Prompt Eval Duration: {PromptEvalDuration}",
            metadata.CreatedAt,
            metadata.EvalCount,
            metadata.EvalDuration,
            metadata.TotalDuration,
            metadata.LoadDuration,
            metadata.PromptEvalCount,
            metadata.PromptEvalDuration);
    }
}
