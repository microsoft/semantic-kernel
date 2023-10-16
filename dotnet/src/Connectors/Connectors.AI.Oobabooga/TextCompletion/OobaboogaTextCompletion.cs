// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
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

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

/// <summary>
/// Oobabooga text completion service API.
/// Adapted from <see href="https://github.com/oobabooga/text-generation-webui/tree/main/api-examples"/>
/// </summary>
[Obsolete("This functionality is available as part of new NuGet package: https://www.nuget.org/packages/MyIA.SemanticKernel.Connectors.AI.Oobabooga/. This will be removed in a future release.")]
public sealed class OobaboogaTextCompletion : ITextCompletion
{
    /// <summary>
    /// The URI path for blocking API requests.
    /// </summary>
    public const string BlockingUriPath = "/api/v1/generate";
    private const string StreamingUriPath = "/api/v1/stream";

    private readonly UriBuilder _blockingUri;
    private readonly UriBuilder _streamingUri;
    private readonly HttpClient _httpClient;
    private readonly Func<ClientWebSocket> _webSocketFactory;
    private readonly bool _useWebSocketsPooling;
    private readonly int _maxNbConcurrentWebSockets;
    private readonly SemaphoreSlim? _concurrentSemaphore;
    private readonly ConcurrentBag<bool>? _activeConnections;
    private readonly ConcurrentBag<ClientWebSocket> _webSocketPool = new();
    private readonly int _keepAliveWebSocketsDuration;
    private readonly ILogger? _logger;
    private Task? _cleanupTask = null;
    private long _lastCallTicks = long.MaxValue;

    /// <summary>
    /// Controls the size of the buffer used to receive websocket packets.
    /// </summary>
    public int WebSocketBufferSize { get; set; } = 2048;

    /// <summary>
    /// Initializes a new instance of the <see cref="OobaboogaTextCompletion"/> class.
    /// </summary>
    /// <param name="endpoint">The service API endpoint to which requests should be sent.</param>
    /// <param name="blockingPort">The port used for handling blocking requests. Default value is 5000</param>
    /// <param name="streamingPort">The port used for handling streaming requests. Default value is 5005</param>
    /// <param name="concurrentSemaphore">You can optionally set a hard limit on the max number of concurrent calls to the either of the completion methods by providing a <see cref="SemaphoreSlim"/>. Calls in excess will wait for existing consumers to release the semaphore</param>
    /// <param name="httpClient">Optional. The HTTP client used for making blocking API requests. If not specified, a default client will be used.</param>
    /// <param name="useWebSocketsPooling">If true, websocket clients will be recycled in a reusable pool as long as concurrent calls are detected</param>
    /// <param name="webSocketsCleanUpCancellationToken">if websocket pooling is enabled, you can provide an optional CancellationToken to properly dispose of the clean up tasks when disposing of the connector</param>
    /// <param name="keepAliveWebSocketsDuration">When pooling is enabled, pooled websockets are flushed on a regular basis when no more connections are made. This is the time to keep them in pool before flushing</param>
    /// <param name="webSocketFactory">The WebSocket factory used for making streaming API requests. Note that only when pooling is enabled will websocket be recycled and reused for the specified duration. Otherwise, a new websocket is created for each call and closed and disposed afterwards, to prevent data corruption from concurrent calls.</param>
    /// <param name="logger">Application logger</param>
    public OobaboogaTextCompletion(Uri endpoint,
        int blockingPort = 5000,
        int streamingPort = 5005,
        SemaphoreSlim? concurrentSemaphore = null,
        HttpClient? httpClient = null,
        bool useWebSocketsPooling = true,
        CancellationToken? webSocketsCleanUpCancellationToken = default,
        int keepAliveWebSocketsDuration = 100,
        Func<ClientWebSocket>? webSocketFactory = null,
        ILogger? logger = null)
    {
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
            this._streamingUri.Scheme = (this._streamingUri.Scheme == "https") ? "wss" : "ws";
        }

        this._httpClient = httpClient ?? new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
        this._useWebSocketsPooling = useWebSocketsPooling;
        this._keepAliveWebSocketsDuration = keepAliveWebSocketsDuration;
        this._logger = logger;
        if (webSocketFactory != null)
        {
            this._webSocketFactory = () =>
            {
                var webSocket = webSocketFactory();
                this.SetWebSocketOptions(webSocket);
                return webSocket;
            };
        }
        else
        {
            this._webSocketFactory = () =>
            {
                ClientWebSocket webSocket = new();
                this.SetWebSocketOptions(webSocket);
                return webSocket;
            };
        }

        // if a hard limit is defined, we use a semaphore to limit the number of concurrent calls, otherwise, we use a stack to track active connections
        if (concurrentSemaphore != null)
        {
            this._concurrentSemaphore = concurrentSemaphore;
            this._maxNbConcurrentWebSockets = concurrentSemaphore.CurrentCount;
        }
        else
        {
            this._activeConnections = new();
            this._maxNbConcurrentWebSockets = 0;
        }

        if (this._useWebSocketsPooling)
        {
            this.StartCleanupTask(webSocketsCleanUpCancellationToken ?? CancellationToken.None);
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(
        string text,
        AIRequestSettings? requestSettings = null,
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
            if (!this._useWebSocketsPooling || !this._webSocketPool.TryTake(out clientWebSocket))
            {
                clientWebSocket = this._webSocketFactory();
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
                if (this._useWebSocketsPooling && clientWebSocket.State == WebSocketState.Open)
                {
                    this._webSocketPool.Add(clientWebSocket);
                }
                else
                {
                    await this.DisposeClientGracefullyAsync(clientWebSocket).ConfigureAwait(false);
                }
            }

            this.FinishConcurrentCall();
        }
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string text,
        AIRequestSettings? requestSettings = null,
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
            httpRequestMessage.Headers.Add("User-Agent", Telemetry.HttpUserAgent);

            using var response = await this._httpClient.SendWithSuccessCheckAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);

            var body = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

            TextCompletionResponse? completionResponse = JsonSerializer.Deserialize<TextCompletionResponse>(body);

            if (completionResponse is null)
            {
                throw new SKException($"Unexpected response from Oobabooga API: {body}");
            }

            return completionResponse.Results.Select(completionText => new TextCompletionResult(completionText)).ToList();
        }
        finally
        {
            this.FinishConcurrentCall();
        }
    }

    #region private ================================================================================

    /// <summary>
    /// Creates an Oobabooga request, mapping dynamic request setting fields to their Oobabooga API counter parts
    /// </summary>
    /// <param name="text">The text to complete.</param>
    /// <param name="requestSettings">The request settings.</param>
    /// <returns>An Oobabooga TextCompletionRequest object with the text and completion parameters.</returns>
    private TextCompletionRequest CreateOobaboogaRequest(string text, AIRequestSettings? requestSettings)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            throw new ArgumentNullException(nameof(text));
        }

        if (requestSettings is null)
        {
            return new TextCompletionRequest()
            {
                Prompt = text
            };
        }

        if (requestSettings is TextCompletionRequest requestSettingsTextCompletionRequest)
        {
            requestSettingsTextCompletionRequest.Prompt = text;
            return requestSettingsTextCompletionRequest;
        }

        var json = JsonSerializer.Serialize(requestSettings);
        var textCompletionRequest = JsonSerializer.Deserialize<TextCompletionRequest>(json);

        if (textCompletionRequest is not null)
        {
            textCompletionRequest.Prompt = text;
            return textCompletionRequest;
        }

        throw new ArgumentException("Invalid request settings, cannot convert to TextCompletionRequest", nameof(requestSettings));
    }

    /// <summary>
    /// Sets the options for the <paramref name="clientWebSocket"/>, either persistent and provided by the ctor, or transient if none provided.
    /// </summary>
    private void SetWebSocketOptions(ClientWebSocket clientWebSocket)
    {
        clientWebSocket.Options.SetRequestHeader("User-Agent", Telemetry.HttpUserAgent);
    }

    /// <summary>
    /// That method is responsible for processing the websocket messages that build a streaming response object. It is crucial that it is run asynchronously to prevent a deadlock with results iteration
    /// </summary>
    private async Task ProcessWebSocketMessagesAsync(ClientWebSocket clientWebSocket, TextCompletionStreamingResult streamingResult, CancellationToken cancellationToken)
    {
        var buffer = new byte[this.WebSocketBufferSize];
        var finishedProcessing = false;
        while (!finishedProcessing && !cancellationToken.IsCancellationRequested)
        {
            MemoryStream messageStream = new();
            WebSocketReceiveResult result;
            do
            {
                var segment = new ArraySegment<byte>(buffer);
                result = await clientWebSocket.ReceiveAsync(segment, cancellationToken).ConfigureAwait(false);
                await messageStream.WriteAsync(buffer, 0, result.Count, cancellationToken).ConfigureAwait(false);
            } while (!result.EndOfMessage);

            messageStream.Seek(0, SeekOrigin.Begin);

            if (result.MessageType == WebSocketMessageType.Text)
            {
                string messageText;
                using (var reader = new StreamReader(messageStream, Encoding.UTF8))
                {
                    messageText = await reader.ReadToEndAsync().ConfigureAwait(false);
                }

                var responseObject = JsonSerializer.Deserialize<TextCompletionStreamingResponse>(messageText);

                if (responseObject is null)
                {
                    throw new SKException($"Unexpected response from Oobabooga API: {messageText}");
                }

                switch (responseObject.Event)
                {
                    case TextCompletionStreamingResponse.ResponseObjectTextStreamEvent:
                        streamingResult.AppendResponse(responseObject);
                        break;
                    case TextCompletionStreamingResponse.ResponseObjectStreamEndEvent:
                        streamingResult.SignalStreamEnd();
                        if (!this._useWebSocketsPooling)
                        {
                            await clientWebSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Acknowledge stream-end oobabooga message", CancellationToken.None).ConfigureAwait(false);
                        }

                        finishedProcessing = true;
                        break;
                    default:
                        break;
                }
            }
            else if (result.MessageType == WebSocketMessageType.Close)
            {
                await clientWebSocket.CloseOutputAsync(WebSocketCloseStatus.NormalClosure, "Acknowledge Close frame", CancellationToken.None).ConfigureAwait(false);
                finishedProcessing = true;
            }

            if (clientWebSocket.State != WebSocketState.Open)
            {
                finishedProcessing = true;
            }
        }
    }

    /// <summary>
    /// Starts a concurrent call, either by taking a semaphore slot or by pushing a value on the active connections stack
    /// </summary>
    /// <param name="cancellationToken"></param>
    private async Task StartConcurrentCallAsync(CancellationToken cancellationToken)
    {
        if (this._concurrentSemaphore != null)
        {
            await this._concurrentSemaphore!.WaitAsync(cancellationToken).ConfigureAwait(false);
        }
        else
        {
            this._activeConnections!.Add(true);
        }
    }

    /// <summary>
    /// Gets the number of concurrent calls, either by reading the semaphore count or by reading the active connections stack count
    /// </summary>
    /// <returns></returns>
    private int GetCurrentConcurrentCallsNb()
    {
        if (this._concurrentSemaphore != null)
        {
            return this._maxNbConcurrentWebSockets - this._concurrentSemaphore!.CurrentCount;
        }

        return this._activeConnections!.Count;
    }

    /// <summary>
    /// Ends a concurrent call, either by releasing a semaphore slot or by popping a value from the active connections stack
    /// </summary>
    private void FinishConcurrentCall()
    {
        if (this._concurrentSemaphore != null)
        {
            this._concurrentSemaphore!.Release();
        }
        else
        {
            this._activeConnections!.TryTake(out _);
        }

        Interlocked.Exchange(ref this._lastCallTicks, DateTime.UtcNow.Ticks);
    }

    private void StartCleanupTask(CancellationToken cancellationToken)
    {
        if (this._cleanupTask == null || this._cleanupTask.IsCompleted)
        {
            this._cleanupTask = Task.Factory.StartNew(
            async () =>
            {
                while (!cancellationToken.IsCancellationRequested)
                {
                    await this.FlushWebSocketClientsAsync(cancellationToken).ConfigureAwait(false);
                }
            },
            cancellationToken,
            TaskCreationOptions.LongRunning,
            TaskScheduler.Default);
        }
    }

    /// <summary>
    /// Flushes the web socket clients that have been idle for too long
    /// </summary>
    /// <returns></returns>
    private async Task FlushWebSocketClientsAsync(CancellationToken cancellationToken)
    {
        // In the cleanup task, make sure you handle OperationCanceledException appropriately
        // and make frequent checks on whether cancellation is requested.
        try
        {
            if (!cancellationToken.IsCancellationRequested)
            {
                await Task.Delay(this._keepAliveWebSocketsDuration, cancellationToken).ConfigureAwait(false);

                // If another call was made during the delay, do not proceed with flushing
                if (DateTime.UtcNow.Ticks - Interlocked.Read(ref this._lastCallTicks) < TimeSpan.FromMilliseconds(this._keepAliveWebSocketsDuration).Ticks)
                {
                    return;
                }

                while (this.GetCurrentConcurrentCallsNb() == 0 && this._webSocketPool.TryTake(out ClientWebSocket clientToDispose))
                {
                    await this.DisposeClientGracefullyAsync(clientToDispose).ConfigureAwait(false);
                }
            }
        }
        catch (OperationCanceledException exception)
        {
            this._logger?.LogTrace(message: "FlushWebSocketClientsAsync cleaning task was cancelled", exception: exception);
            while (this._webSocketPool.TryTake(out ClientWebSocket clientToDispose))
            {
                await this.DisposeClientGracefullyAsync(clientToDispose).ConfigureAwait(false);
            }
        }
    }

    /// <summary>
    /// Closes and disposes of a client web socket after use
    /// </summary>
    private async Task DisposeClientGracefullyAsync(ClientWebSocket clientWebSocket)
    {
        try
        {
            if (clientWebSocket.State == WebSocketState.Open)
            {
                await clientWebSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing client before disposal", CancellationToken.None).ConfigureAwait(false);
            }
        }
        catch (OperationCanceledException exception)
        {
            this._logger?.LogTrace(message: "Closing client web socket before disposal was cancelled", exception: exception);
        }
        catch (WebSocketException exception)
        {
            this._logger?.LogTrace(message: "Closing client web socket before disposal raised web socket exception", exception: exception);
        }
        finally
        {
            clientWebSocket.Dispose();
        }
    }

    #endregion
}
