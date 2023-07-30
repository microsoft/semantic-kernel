// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.WebSockets;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

/// <summary>
/// Oobabooga text completion service API.
/// Adapted from <see href="https://github.com/oobabooga/text-generation-webui/tree/main/api-examples"/>
/// </summary>
public sealed class OobaboogaChatCompletion : OobaboogaCompletionBase, IChatCompletion
{
    private readonly UriBuilder _chatBlockingUri;
    private readonly UriBuilder _chatStreamingUri;

    public const string ChatBlockingUriPath = "/api/v1/chat";
    public const string ChatStreamingUriPath = "/api/v1/chat-stream";

    public ChatCompletionOobaboogaSettings ChatCompletionOobaboogaSettings { get; set; }

    /// <inheritdoc/>
    public OobaboogaChatCompletion(Uri endpoint, int blockingPort = 5000,
        int streamingPort = 5005,
        ChatCompletionOobaboogaSettings? chatCompletionRequestSettings = null,
        SemaphoreSlim? concurrentSemaphore = null,
        HttpClient? httpClient = null,
        bool useWebSocketsPooling = true,
        CancellationToken? webSocketsCleanUpCancellationToken = default,
        int keepAliveWebSocketsDuration = 100,
        Func<ClientWebSocket>? webSocketFactory = null,
        ILogger? logger = null) : base(endpoint, blockingPort, streamingPort, concurrentSemaphore, httpClient, useWebSocketsPooling, webSocketsCleanUpCancellationToken, keepAliveWebSocketsDuration, webSocketFactory, logger)
    {
        this.ChatCompletionOobaboogaSettings = chatCompletionRequestSettings ?? new ChatCompletionOobaboogaSettings();
        this._chatBlockingUri = new(endpoint)
        {
            Port = blockingPort,
            Path = ChatBlockingUriPath
        };
        this._chatStreamingUri = new(endpoint)
        {
            Port = streamingPort,
            Path = ChatStreamingUriPath
        };
        if (this._chatStreamingUri.Uri.Scheme.StartsWith("http", StringComparison.OrdinalIgnoreCase))
        {
            this._chatStreamingUri.Scheme = this._chatStreamingUri.Scheme == "https" ? "wss" : "ws";
        }
    }

    public SemanticKernel.AI.ChatCompletion.ChatHistory CreateNewChat(string? instructions = null)
    {
        return new SemanticKernel.AI.ChatCompletion.ChatHistory();
    }

    public async Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        SemanticKernel.AI.ChatCompletion.ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await this.StartConcurrentCallAsync(cancellationToken).ConfigureAwait(false);

            var completionRequest = this.CreateOobaboogaChatRequest(chat, requestSettings);

            using var stringContent = new StringContent(
                JsonSerializer.Serialize(completionRequest),
                Encoding.UTF8,
                "application/json");

            using var httpRequestMessage = new HttpRequestMessage()
            {
                Method = HttpMethod.Post,
                RequestUri = this._chatBlockingUri.Uri,
                Content = stringContent
            };
            httpRequestMessage.Headers.Add("User-Agent", HttpUserAgent);

            using var response = await this.HTTPClient.SendAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();

            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            ChatCompletionResponse? completionResponse = null;
            if (!string.IsNullOrEmpty(body))
            {
                completionResponse = JsonSerializer.Deserialize<ChatCompletionResponse>(body);
            }

            if (completionResponse is null)
            {
                throw new OobaboogaInvalidResponseException<string>(body, "Unexpected response from Oobabooga API");
            }

            return completionResponse.Results.ConvertAll(result => new ChatCompletionResult(result));
        }
        catch (Exception e) when (e is not AIException && !e.IsCriticalException())
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
        finally
        {
            this.FinishConcurrentCall();
        }
    }

    public async IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        SemanticKernel.AI.ChatCompletion.ChatHistory chat,
        ChatRequestSettings? requestSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await this.StartConcurrentCallAsync(cancellationToken).ConfigureAwait(false);

        var completionRequest = this.CreateOobaboogaChatRequest(chat, requestSettings);

        var requestJson = JsonSerializer.Serialize(completionRequest);

        var requestBytes = Encoding.UTF8.GetBytes(requestJson);

        ClientWebSocket? clientWebSocket = null;
        try
        {
            // if pooling is enabled, web socket is going to be recycled for reuse, if not it will be properly disposed of after the call
#pragma warning disable CA2000 // Dispose objects before losing scope
            if (!this.UseWebSocketsPooling || !this.WebSocketPool.TryTake(out clientWebSocket))
            {
                clientWebSocket = this.WebSocketFactory();
            }
#pragma warning restore CA2000 // Dispose objects before losing scope
            if (clientWebSocket.State == WebSocketState.None)
            {
                await clientWebSocket.ConnectAsync(this._chatStreamingUri.Uri, cancellationToken).ConfigureAwait(false);
            }

            var sendSegment = new ArraySegment<byte>(requestBytes);
            await clientWebSocket.SendAsync(sendSegment, WebSocketMessageType.Text, true, cancellationToken).ConfigureAwait(false);

            ChatCompletionStreamingResult streamingResult = new();

            var processingTask = this.ProcessWebSocketMessagesAsync(clientWebSocket, streamingResult, cancellationToken);

            yield return streamingResult;

            await processingTask.ConfigureAwait(false);
        }
        finally
        {
            if (clientWebSocket != null)
            {
                if (this.UseWebSocketsPooling && clientWebSocket.State == WebSocketState.Open)
                {
                    this.WebSocketPool.Add(clientWebSocket);
                }
                else
                {
                    await this.DisposeClientGracefullyAsync(clientWebSocket).ConfigureAwait(false);
                }
            }

            this.FinishConcurrentCall();
        }
    }

    private ChatCompletionRequest CreateOobaboogaChatRequest(SemanticKernel.AI.ChatCompletion.ChatHistory chat, ChatRequestSettings? requestSettings)
    {
        if (chat is null)
        {
            throw new ArgumentNullException(nameof(chat));
        }

        if (requestSettings is null)
        {
            requestSettings = new ChatRequestSettings();
        }

        var completionRequest = ChatCompletionRequest.Create(chat, this.ChatCompletionOobaboogaSettings, requestSettings);
        return completionRequest;
    }

    protected override CompletionStreamingResponseBase? GetResponseObject(string messageText)
    {
        return JsonSerializer.Deserialize<ChatCompletionStreamingResponse>(messageText);
    }
}
