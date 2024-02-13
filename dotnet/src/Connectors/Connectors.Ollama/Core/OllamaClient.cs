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

    public async Task<IReadOnlyList<TextContent>> GenerateTextAsync(string prompt, PromptExecutionSettings executionSettings, CancellationToken cancellationToken)
    {
        var endpoint = this.EndpointProvider.TextGenerationEndpoint;
        var request = CreateTextRequest(prompt, executionSettings);
        using var httpRequestMessage = this.HttpRequestFactory.CreatePost(request, endpoint);

        string body = await this.SendRequestAndGetStringBodyAsync(httpRequestMessage, cancellationToken)
            .ConfigureAwait(false);

        var response = JsonSerializer.Deserialize<OllamaTextResponse>(body);


    }

    private List<ChatMessageContent> GetChatMessageContentsFromResponse(OllamaChatResponse response)
    {
        return new List<ChatMessageContent>
        {
            new(
                role: response.Message?.Role ?? AuthorRole.Assistant,
                content: response.Message?.Content ?? string.Empty,
                modelId: this._modelId,
                innerContent: response,
                metadata: GetResponseMetadata(response))
        };
    }

    private IReadOnlyDictionary<string, object?>? GetResponseMetadata(OllamaChatResponse response)
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
        var endpoint = this.EndpointProvider.StreamChatCompletionEndpoint;
        var request = CreateChatRequest(chatHistory, executionSettings);
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

    protected static OllamaChatRequest CreateChatRequest(
        ChatHistory chatHistory,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(ollamaExecutionSettings.MaxTokens);
        var request = OllamaChatRequest.FromPromptAndExecutionSettings(chatHistory, ollamaExecutionSettings);
        return request;
    }

    protected static OllamaTextRequest CreateTextRequest(
        string prompt,
        PromptExecutionSettings? promptExecutionSettings)
    {
        var ollamaExecutionSettings = OllamaPromptExecutionSettings.FromExecutionSettings(promptExecutionSettings);
        ValidateMaxTokens(ollamaExecutionSettings.MaxTokens);
        var request = OllamaTextRequest.FromPromptAndExecutionSettings(prompt, ollamaExecutionSettings);
        return request;
    }
}
