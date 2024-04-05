// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Represents a client for interacting with the chat completion Claude models.
/// </summary>
internal sealed class ClaudeChatCompletionClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger _logger;
    private readonly string _modelId;
    private readonly Uri _endpoint;
    private readonly Func<HttpRequestMessage, Task>? _customRequestHandler;

    /// <summary>
    /// Represents a client for interacting with the chat completion Claude model.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting chat completion</param>
    /// <param name="apiKey">Api key</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public ClaudeChatCompletionClient(
        HttpClient httpClient,
        string modelId,
        string apiKey,
        ILogger? logger = null)
    {
        Verify.NotNull(httpClient);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
        this._modelId = modelId;
        this._endpoint = new Uri("https://api.anthropic.com/v1/messages");
    }

    /// <summary>
    /// Represents a client for interacting with the chat completion Claude model.
    /// </summary>
    /// <param name="httpClient">HttpClient instance used to send HTTP requests</param>
    /// <param name="modelId">Id of the model supporting chat completion</param>
    /// <param name="endpoint">Endpoint for the chat completion model</param>
    /// <param name="requestHandler">A custom request handler to be used for sending HTTP requests</param>
    /// <param name="logger">Logger instance used for logging (optional)</param>
    public ClaudeChatCompletionClient(
        HttpClient httpClient,
        string modelId,
        Uri endpoint,
        Func<HttpRequestMessage, Task>? requestHandler,
        ILogger? logger = null)
    {
        Verify.NotNull(httpClient);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(endpoint);

        this._httpClient = httpClient;
        this._logger = logger ?? NullLogger.Instance;
        this._modelId = modelId;
        this._endpoint = endpoint;
        this._customRequestHandler = requestHandler;
    }

    /// <summary>
    /// Generates a chat message asynchronously.
    /// </summary>
    /// <param name="chatHistory">The chat history containing the conversation data.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="kernel">A kernel instance.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>Returns a list of chat message contents.</returns>
    public async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        await Task.Yield();
        throw new NotImplementedException("Implement this method in next PR.");
    }

    /// <summary>
    /// Generates a stream of chat messages asynchronously.
    /// </summary>
    /// <param name="chatHistory">The chat history containing the conversation data.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="kernel">A kernel instance.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>An asynchronous enumerable of <see cref="StreamingChatMessageContent"/> streaming chat contents.</returns>
    public async IAsyncEnumerable<StreamingChatMessageContent> StreamGenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await Task.Yield();
        throw new NotImplementedException("Implement this method in next PR.");
        yield break;
    }

    private static void ValidateMaxTokens(int? maxTokens)
    {
        // If maxTokens is null, it means that the user wants to use the default model value
        if (maxTokens is < 1)
        {
            throw new ArgumentException($"MaxTokens {maxTokens} is not valid, the value must be greater than zero");
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

    private async Task<HttpResponseMessage> SendRequestAndGetResponseImmediatelyAfterHeadersReadAsync(
        HttpRequestMessage httpRequestMessage,
        CancellationToken cancellationToken)
    {
        var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
            .ConfigureAwait(false);
        return response;
    }

    private static T DeserializeResponse<T>(string body)
    {
        try
        {
            return JsonSerializer.Deserialize<T>(body) ?? throw new JsonException("Response is null");
        }
        catch (JsonException exc)
        {
            throw new KernelException("Unexpected response from model", exc)
            {
                Data = { { "ResponseData", body } },
            };
        }
    }

    private async Task<HttpRequestMessage> CreateHttpRequestAsync(object requestData, Uri endpoint)
    {
        var httpRequestMessage = HttpRequest.CreatePostRequest(endpoint, requestData);
        httpRequestMessage.Headers.Add("User-Agent", HttpHeaderConstant.Values.UserAgent);
        httpRequestMessage.Headers.Add(HttpHeaderConstant.Names.SemanticKernelVersion,
            HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ClaudeChatCompletionClient)));

        if (this._customRequestHandler != null)
        {
            await this._customRequestHandler(httpRequestMessage).ConfigureAwait(false);
        }

        return httpRequestMessage;
    }

    private void Log(LogLevel logLevel, string? message, params object[] args)
    {
        if (this._logger.IsEnabled(logLevel))
        {
#pragma warning disable CA2254 // Template should be a constant string.
            this._logger.Log(logLevel, message, args);
#pragma warning restore CA2254
        }
    }
}
