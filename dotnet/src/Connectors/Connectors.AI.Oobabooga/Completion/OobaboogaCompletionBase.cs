// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Net.Http;
using System.Net.WebSockets;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion;

public abstract class OobaboogaCompletionBase<TCompletionInput, TRequestSettings, TOobaboogaSettings, TCompletionRequest, TCompletionResponse, TCompletionResult, TCompletionStreamingResult> : OobaboogaCompletionBase
    where TCompletionStreamingResult : CompletionStreamingResultBase, new()
    where TOobaboogaSettings : new()

{
    private readonly UriBuilder _blockingUri;
    private readonly UriBuilder _streamingUri;
    private protected readonly TOobaboogaSettings OobaboogaSettings;

    protected OobaboogaCompletionBase(Uri endpoint,
        string blockingPath,
        string streamingPath,
        int blockingPort = 5000,
        int streamingPort = 5005,
        TOobaboogaSettings? oobaboogaSettings = default,
        SemaphoreSlim? concurrentSemaphore = null,
        HttpClient? httpClient = null,
        bool useWebSocketsPooling = true,
        CancellationToken? webSocketsCleanUpCancellationToken = null,
        int keepAliveWebSocketsDuration = 100,
        Func<ClientWebSocket>? webSocketFactory = null,
        ILogger? logger = null) : base(endpoint, blockingPort, streamingPort, concurrentSemaphore, httpClient, useWebSocketsPooling, webSocketsCleanUpCancellationToken, keepAliveWebSocketsDuration, webSocketFactory, logger)
    {
        Verify.NotNull(endpoint);
        this.OobaboogaSettings = oobaboogaSettings ?? new();

        this._blockingUri = new UriBuilder(endpoint)
        {
            Port = blockingPort,
            Path = blockingPath
        };
        this._streamingUri = new(endpoint)
        {
            Port = streamingPort,
            Path = streamingPath
        };
        if (this._streamingUri.Uri.Scheme.StartsWith("http", StringComparison.OrdinalIgnoreCase))
        {
            this._streamingUri.Scheme = this._streamingUri.Scheme == "https" ? "wss" : "ws";
        }
    }

    public async Task<IReadOnlyList<TCompletionResult>> GetCompletionsBaseAsync(
        TCompletionInput input,
        TRequestSettings? requestSettings,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await this.StartConcurrentCallAsync(cancellationToken).ConfigureAwait(false);

            var completionRequest = this.CreateCompletionRequest(input, requestSettings);

            using var httpRequestMessage = HttpRequest.CreatePostRequest(this._blockingUri.Uri, completionRequest);
            httpRequestMessage.Headers.Add("User-Agent", Telemetry.HttpUserAgent);

            using var response = await this.HttpClient.SendAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();

            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            TCompletionResponse? completionResponse = JsonSerializer.Deserialize<TCompletionResponse>(body);

            if (completionResponse is null)
            {
                throw new SKException($"Unexpected response from Oobabooga API:\n{body}");
            }

            return this.GetCompletionResults(completionResponse);
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

    public async IAsyncEnumerable<TCompletionStreamingResult> GetStreamingCompletionsBaseAsync(
        TCompletionInput input,
        TRequestSettings? requestSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await this.StartConcurrentCallAsync(cancellationToken).ConfigureAwait(false);

        var completionRequest = this.CreateCompletionRequest(input, requestSettings);

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

            TCompletionStreamingResult streamingResult = new();

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

    protected abstract IReadOnlyList<TCompletionResult> GetCompletionResults([DisallowNull] TCompletionResponse completionResponse);

    protected abstract TCompletionRequest CreateCompletionRequest(TCompletionInput input, TRequestSettings? requestSettings);
}

public abstract class OobaboogaCompletionBase
{
    private protected readonly HttpClient HttpClient;
    private protected readonly Func<ClientWebSocket> WebSocketFactory;
    private protected readonly bool UseWebSocketsPooling;
    private readonly int _maxNbConcurrentWebSockets;
    private readonly SemaphoreSlim? _concurrentSemaphore;
    private readonly ConcurrentBag<bool>? _activeConnections;
    internal readonly ConcurrentBag<ClientWebSocket> WebSocketPool = new();
    private readonly int _keepAliveWebSocketsDuration;
    private readonly ILogger? _logger;
    private long _lastCallTicks = long.MaxValue;

    /// <summary>
    /// Controls the size of the buffer used to received websocket packets
    /// </summary>
    public int WebSocketBufferSize { get; set; } = 2048;

    /// <summary>
    /// Initializes a new instance of the <see cref="OobaboogaCompletionBase"/> class.
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
    protected OobaboogaCompletionBase(Uri endpoint,
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
        this.HttpClient = httpClient ?? new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);
        this.UseWebSocketsPooling = useWebSocketsPooling;
        this._keepAliveWebSocketsDuration = keepAliveWebSocketsDuration;
        this._logger = logger;
        if (webSocketFactory != null)
        {
            this.WebSocketFactory = () =>
            {
                var webSocket = webSocketFactory();
                this.SetWebSocketOptions(webSocket);
                return webSocket;
            };
        }
        else
        {
            this.WebSocketFactory = () =>
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

        if (this.UseWebSocketsPooling)
        {
            this.StartCleanupTask(webSocketsCleanUpCancellationToken ?? CancellationToken.None);
        }
    }

    /// <summary>
    /// That method is responsible for processing the websocket messages that build a streaming response object. It is crucial that it is run asynchronously to prevent a deadlock with results iteration
    /// </summary>
    protected async Task ProcessWebSocketMessagesAsync(ClientWebSocket clientWebSocket, CompletionStreamingResultBase streamingResult, CancellationToken cancellationToken)
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

                var responseObject = this.GetResponseObject(messageText);

                if (responseObject is null)
                {
                    throw new SKException($"Unexpected response from Oobabooga API: {messageText}");
                }

                switch (responseObject.Event)
                {
                    case CompletionStreamingResponseBase.ResponseObjectTextStreamEvent:
                        streamingResult.AppendResponse(responseObject);
                        break;
                    case CompletionStreamingResponseBase.ResponseObjectStreamEndEvent:
                        streamingResult.SignalStreamEnd();
                        if (!this.UseWebSocketsPooling)
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

    protected abstract CompletionStreamingResponseBase? GetResponseObject(string messageText);

    /// <summary>
    /// Starts a concurrent call, either by taking a semaphore slot or by pushing a value on the active connections stack
    /// </summary>
    /// <param name="cancellationToken"></param>
    protected async Task StartConcurrentCallAsync(CancellationToken cancellationToken)
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
    /// Ends a concurrent call, either by releasing a semaphore slot or by popping a value from the active connections stack
    /// </summary>
    protected void FinishConcurrentCall()
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

    /// <summary>
    /// Closes and disposes of a client web socket after use
    /// </summary>
    protected async Task DisposeClientGracefullyAsync(ClientWebSocket clientWebSocket)
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

    #region private ================================================================================

    /// <summary>
    /// Sets the options for the <paramref name="clientWebSocket"/>, either persistent and provided by the ctor, or transient if none provided.
    /// </summary>
    private void SetWebSocketOptions(ClientWebSocket clientWebSocket)
    {
        clientWebSocket.Options.SetRequestHeader("User-Agent", Telemetry.HttpUserAgent);
    }

    /// <summary>
    /// Gets the number of concurrent calls, either by reading the semaphore count or by reading the active connections stack count
    /// </summary>
    private int GetCurrentConcurrentCallsNb()
    {
        if (this._concurrentSemaphore != null)
        {
            return this._maxNbConcurrentWebSockets - this._concurrentSemaphore!.CurrentCount;
        }

        return this._activeConnections!.Count;
    }

    private void StartCleanupTask(CancellationToken cancellationToken)
    {
        Task.Factory.StartNew<Task>(
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

    /// <summary>
    /// Flushes the web socket clients that have been idle for too long
    /// </summary>
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

                while (this.GetCurrentConcurrentCallsNb() == 0 && this.WebSocketPool.TryTake(out ClientWebSocket clientToDispose))
                {
                    await this.DisposeClientGracefullyAsync(clientToDispose).ConfigureAwait(false);
                }
            }
        }
        catch (OperationCanceledException exception)
        {
            this._logger?.LogTrace(message: "FlushWebSocketClientsAsync cleaning task was cancelled", exception: exception);
            while (this.WebSocketPool.TryTake(out ClientWebSocket clientToDispose))
            {
                await this.DisposeClientGracefullyAsync(clientToDispose).ConfigureAwait(false);
            }
        }
    }

    /// <summary>
    /// Logs Oobabooga action details.
    /// </summary>
    /// <param name="callerMemberName">Caller member name. Populated automatically by runtime.</param>
    private protected void LogActionDetails([CallerMemberName] string? callerMemberName = default)
    {
        this._logger?.LogInformation("Oobabooga Action: {Action}.", callerMemberName);
    }

    #endregion
}
