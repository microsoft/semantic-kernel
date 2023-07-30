// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.WebSockets;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.TextCompletion;

public class OobaboogaTextCompletion : OobaboogaCompletionBase, ITextCompletion
{
    public const string BlockingUriPath = "/api/v1/generate";
    private const string StreamingUriPath = "/api/v1/stream";

    private readonly UriBuilder _blockingUri;
    private readonly UriBuilder _streamingUri;

    public CompletionOobaboogaSettings CompletionOobaboogaSettings { get; set; }

    /// <inheritdoc/>
    public OobaboogaTextCompletion(Uri endpoint,
        int blockingPort = 5000,
        int streamingPort = 5005,
        CompletionOobaboogaSettings? completionRequestSettings = null,
        SemaphoreSlim? concurrentSemaphore = null,
        HttpClient? httpClient = null,
        bool useWebSocketsPooling = true,
        CancellationToken? webSocketsCleanUpCancellationToken = default,
        int keepAliveWebSocketsDuration = 100,
        Func<ClientWebSocket>? webSocketFactory = null,
        ILogger? logger = null) : base(endpoint, blockingPort, streamingPort, concurrentSemaphore, httpClient, useWebSocketsPooling, webSocketsCleanUpCancellationToken, keepAliveWebSocketsDuration, webSocketFactory, logger)
    {
        this.CompletionOobaboogaSettings = completionRequestSettings ?? new CompletionOobaboogaSettings();
        Verify.NotNull(endpoint);
        this._blockingUri = new UriBuilder(endpoint)
        {
            Port = blockingPort,
            Path = BlockingUriPath
        };
        this._streamingUri = new(endpoint)
        {
            Port = streamingPort,
            Path = StreamingUriPath
        };
        if (this._streamingUri.Uri.Scheme.StartsWith("http", StringComparison.OrdinalIgnoreCase))
        {
            this._streamingUri.Scheme = this._streamingUri.Scheme == "https" ? "wss" : "ws";
        }
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string text,
        CompleteRequestSettings requestSettings,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await this.StartConcurrentCallAsync(cancellationToken).ConfigureAwait(false);

            var completionRequest = this.CreateOobaboogaRequest(text, requestSettings);

            using var stringContent = new StringContent(
                JsonSerializer.Serialize(completionRequest),
                Encoding.UTF8,
                "application/json");

            using var httpRequestMessage = new HttpRequestMessage()
            {
                Method = HttpMethod.Post,
                RequestUri = this._blockingUri.Uri,
                Content = stringContent
            };
            httpRequestMessage.Headers.Add("User-Agent", HttpUserAgent);

            using var response = await this.HTTPClient.SendAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();

            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            TextCompletionResponse? completionResponse = JsonSerializer.Deserialize<TextCompletionResponse>(body);

            if (completionResponse is null)
            {
                throw new OobaboogaInvalidResponseException<string>(body, "Unexpected response from Oobabooga API");
            }

            return completionResponse.Results.Select(completionText => new TextCompletionResult(completionText)).ToList();
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

    /// <inheritdoc/>
    public async IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(
        string text,
        CompleteRequestSettings requestSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await this.StartConcurrentCallAsync(cancellationToken).ConfigureAwait(false);

        var completionRequest = this.CreateOobaboogaRequest(text, requestSettings);

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
                await clientWebSocket.ConnectAsync(this._streamingUri.Uri, cancellationToken).ConfigureAwait(false);
            }

            var sendSegment = new ArraySegment<byte>(requestBytes);
            await clientWebSocket.SendAsync(sendSegment, WebSocketMessageType.Text, true, cancellationToken).ConfigureAwait(false);

            TextCompletionStreamingResult streamingResult = new();

            var processingTask = this.ProcessWebSocketMessagesAsync(clientWebSocket, streamingResult, cancellationToken);

            yield return streamingResult;

            // Await the processing task to make sure it's finished before continuing
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

    /// <summary>
    /// Creates an Oobabooga request, mapping CompleteRequestSettings fields to their Oobabooga API counter parts
    /// </summary>
    /// <param name="text">The text to complete.</param>
    /// <param name="requestSettings">The request settings.</param>
    /// <returns>An Oobabooga TextCompletionRequest object with the text and completion parameters.</returns>
    private CompletionRequest CreateOobaboogaRequest(string text, CompleteRequestSettings requestSettings)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            throw new ArgumentNullException(nameof(text));
        }

        // Prepare the request using the provided parameters.
        var toReturn = CompletionRequest.Create(text, this.CompletionOobaboogaSettings, requestSettings);
        return toReturn;
    }
}
