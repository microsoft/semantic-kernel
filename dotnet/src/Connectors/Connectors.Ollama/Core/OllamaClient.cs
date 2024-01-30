// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Logging;
using System.Text.Json;
using System.Threading.Tasks;
using System.Threading;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;
internal abstract class OllamaClient : IOllamaClient
{
    private readonly string _modelId;
    protected IHttpRequestFactory HttpRequestFactory { get; }
    protected IEndpointProvider EndpointProvider { get; }
    protected HttpClient HttpClient { get; }
    protected ILogger Logger { get; }

    protected OllamaClient(
        string modelId,
        HttpClient httpClient,
        IHttpRequestFactory httpRequestFactory,
        IEndpointProvider endpointProvider,
        ILogger? logger)
    {
        this._modelId = modelId;
        this.HttpClient = httpClient;
        this.HttpRequestFactory = httpRequestFactory;
        this.EndpointProvider = endpointProvider;
        this.Logger = logger ?? NullLogger.Instance;
    }

    protected static void ValidateMaxTokens(int? maxTokens)
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
        using var response = await this.HttpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        var body = await response.Content.ReadAsStringWithExceptionMappingAsync()
            .ConfigureAwait(false);
        return body;
    }

    protected async Task<HttpResponseMessage> SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        var response = await this.HttpClient.SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
            .ConfigureAwait(false);
        return response;
    }

    protected static T DeserializeResponse<T>(string body)
    {
        try
        {
            T? geminiResponse = JsonSerializer.Deserialize<T>(body);
            if (geminiResponse is null)
            {
                throw new JsonException("Response is null");
            }

            return geminiResponse;
        }
        catch (JsonException exc)
        {
            throw new KernelException("Unexpected response from model", exc)
            {
                Data = { { "ResponseData", body } },
            };
        }
    }

    public Task<IReadOnlyList<TextContent>> GenerateTextAsync(string prompt, PromptExecutionSettings executionSettings, CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }

    public IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(string prompt, PromptExecutionSettings? executionSettings = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public virtual async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        var endpoint = this.EndpointProvider.ChatCompletionEndpoint;
        var request = CreateChatRequest(chatHistory, executionSettings);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(request, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        throw new NotImplementedException();
    }


    /// <inheritdoc/>
    public virtual async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var endpoint = this.EndpointProvider.StreamChatCompletionEndpoint(this._modelId);
        var request = CreateRequest(chatHistory, executionSettings);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(request, endpoint);

        using var response = await this.SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);
        using var responseStream = await response.Content.ReadAsStreamAndTranslateExceptionAsync()
            .ConfigureAwait(false);

        await foreach (var streamingChatMessageContent in this.StreamGenerateChatMessageAsync(chatHistory, executionSettings, cancellationToken))
        {
            yield return streamingChatMessageContent;
        }
    }

    protected static OllamaRequest CreateChatRequest(
        ChatHistory chatHistory,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var ollamaExecutionSettings = OllamaExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(ollamaExecutionSettings.MaxTokens);
        var request = OllamaRequest.FromPromptAndExecutionSettings(chatHistory, ollamaExecutionSettings);
        return request;
    }

    private OllamaChatRequest CreateChatRequest(ChatHistory chatHistory, bool stream = false)
    {
        return new OllamaChatRequest()
        {
            Model = this._modelId,
            Stream = stream,
            Messages = chatHistory,
        };
    }
    private OllamaRequest CreateRequest(string prompt, bool stream = false)
    {
        return new OllamaRequest()
        {
            Model = this._modelId,
            Stream = stream,
            Prompt = prompt
        };
    }
}
