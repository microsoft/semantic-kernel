// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.WebSockets;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace SemanticKernel.Connectors.UnitTests;

internal class WebSocketTestServer : IDisposable
{
    private readonly ILogger? _logger;

    private readonly HttpListener _httpListener;
    private readonly CancellationTokenSource _mainCancellationTokenSource;
    private readonly CancellationTokenSource _socketCancellationTokenSource;
    private bool _serverIsRunning;

    public Func<ArraySegment<byte>, List<ArraySegment<byte>>>? ArraySegmentHandler { get; set; }
    private readonly ConcurrentDictionary<Guid, ConcurrentQueue<byte[]>> _requestContentQueues;
    private readonly ConcurrentBag<Task> _runningTasks = new();

    private readonly ConcurrentDictionary<Guid, ConnectedClient> _clients = new();

    public TimeSpan RequestProcessingDelay { get; set; } = TimeSpan.Zero;
    public TimeSpan SegmentMessageDelay { get; set; } = TimeSpan.Zero;

    public ConcurrentDictionary<Guid, byte[]> RequestContents
    {
        get
        {
            return new ConcurrentDictionary<Guid, byte[]>(
                this._requestContentQueues
                    .ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList().SelectMany(bytes => bytes).ToArray()));
        }
    }

    public WebSocketTestServer(string url, Func<ArraySegment<byte>, List<ArraySegment<byte>>>? arraySegmentHandler = null, ILogger? logger = null)
    {
        this._logger = logger;

        if (arraySegmentHandler != null)
        {
            this.ArraySegmentHandler = arraySegmentHandler;
        }

        this._requestContentQueues = new ConcurrentDictionary<Guid, ConcurrentQueue<byte[]>>();

        this._mainCancellationTokenSource = new();
        this._socketCancellationTokenSource = new();

        this._httpListener = new HttpListener();
        this._httpListener.Prefixes.Add(url);
        this._httpListener.Start();
        this._serverIsRunning = true;

        Task.Run((Func<Task>)this.HandleRequestsAsync, this._mainCancellationTokenSource.Token);
    }

    private async Task HandleRequestsAsync()
    {
        while (!this._mainCancellationTokenSource.IsCancellationRequested)
        {
            var context = await this._httpListener.GetContextAsync().ConfigureAwait(false);

            if (this._serverIsRunning)
            {
                if (context.Request.IsWebSocketRequest)
                {
                    var connectedClient = new ConnectedClient(Guid.NewGuid(), context);
                    this._clients[connectedClient.Id] = connectedClient;
                    try
                    {
                        var socketContext = await context.AcceptWebSocketAsync(subProtocol: null);
                        connectedClient.SetSocket(socketContext.WebSocket);
                        this._runningTasks.Add(this.HandleSingleWebSocketRequestAsync(connectedClient));
                    }
                    catch
                    {
                        // server error if upgrade from HTTP to WebSocket fails
                        context.Response.StatusCode = 500;
                        context.Response.StatusDescription = "WebSocket upgrade failed";
                        context.Response.Close();
                        throw;
                    }
                }
            }
            else
            {
                // HTTP 409 Conflict (with server's current state)
                context.Response.StatusCode = 409;
                context.Response.StatusDescription = "Server is shutting down";
                context.Response.Close();
                return;
            }
        }

        await Task.WhenAll(this._runningTasks).ConfigureAwait(false);
    }

    private async Task HandleSingleWebSocketRequestAsync(ConnectedClient connectedClient)
    {
        var buffer = WebSocket.CreateServerBuffer(4096);

        Guid requestId = connectedClient.Id;
        this._requestContentQueues[requestId] = new ConcurrentQueue<byte[]>();

        try
        {
            while (!this._socketCancellationTokenSource.IsCancellationRequested && connectedClient.Socket != null && connectedClient.Socket.State != WebSocketState.Closed && connectedClient.Socket.State != WebSocketState.Aborted)
            {
                WebSocketReceiveResult result = await connectedClient.Socket.ReceiveAsync(buffer, this._socketCancellationTokenSource.Token).ConfigureAwait(false);
                if (!this._socketCancellationTokenSource.IsCancellationRequested && connectedClient.Socket.State != WebSocketState.Closed && connectedClient.Socket.State != WebSocketState.Aborted)
                {
                    if (connectedClient.Socket.State == WebSocketState.CloseReceived && result.MessageType == WebSocketMessageType.Close)
                    {
                        await connectedClient.Socket.CloseOutputAsync(WebSocketCloseStatus.NormalClosure, "Acknowledge Close frame", CancellationToken.None);

                        break;
                    }

                    var receivedBytes = buffer.Slice(0, result.Count);
                    this._requestContentQueues[requestId].Enqueue(receivedBytes.ToArray());

                    if (result.EndOfMessage)
                    {
                        var responseSegments = this.ArraySegmentHandler?.Invoke(receivedBytes);

                        if (this.RequestProcessingDelay.Ticks > 0)
                        {
                            await Task.Delay(this.RequestProcessingDelay).ConfigureAwait(false);
                        }

                        if (responseSegments != null)
                        {
                            foreach (var responseSegment in responseSegments)
                            {
                                if (connectedClient.Socket.State != WebSocketState.Open)
                                {
                                    break;
                                }

                                if (this.SegmentMessageDelay.Ticks > 0)
                                {
                                    await Task.Delay(this.SegmentMessageDelay).ConfigureAwait(false);
                                }

                                await connectedClient.Socket.SendAsync(responseSegment, WebSocketMessageType.Text, true, this._socketCancellationTokenSource.Token).ConfigureAwait(false);
                            }
                        }
                    }
                }
            }

            if (connectedClient.Socket?.State == WebSocketState.Open)
            {
                await connectedClient.Socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing waiting for acknowledgement", CancellationToken.None).ConfigureAwait(false);
            }
            else if (connectedClient.Socket?.State == WebSocketState.CloseReceived)
            {
                await connectedClient.Socket.CloseOutputAsync(WebSocketCloseStatus.NormalClosure, "Closing without waiting for acknowledgment", CancellationToken.None).ConfigureAwait(false);
            }
        }
        catch (OperationCanceledException exception)
        {
            this._logger?.LogTrace(message: "Closing server web socket before disposal was cancelled", exception: exception);
        }
        catch (WebSocketException exception)
        {
            this._logger?.LogTrace(message: "Closing server web socket before disposal raised web socket exception", exception: exception);
        }
        finally
        {
            if (connectedClient.Socket?.State != WebSocketState.Closed)
            {
                connectedClient.Socket?.Abort();
            }

            connectedClient.Socket?.Dispose();

            // Remove client from dictionary when done
            this._clients.TryRemove(requestId, out _);
        }
    }

    private async Task CloseAllSocketsAsync()
    {
        // Close all active sockets before disposing
        foreach (var client in this._clients.Values)
        {
            if (client.Socket?.State == WebSocketState.Open)
            {
                await client.Socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", this._mainCancellationTokenSource.Token).ConfigureAwait(false);
            }
        }
    }

    public async ValueTask DisposeAsync()
    {
        try
        {
            this._serverIsRunning = false;
            await this.CloseAllSocketsAsync(); // Close all sockets before finishing the tasks
            await Task.WhenAll(this._runningTasks).ConfigureAwait(false);
            this._socketCancellationTokenSource.Cancel();
            this._mainCancellationTokenSource.Cancel();
        }
        catch (OperationCanceledException exception)
        {
            this._logger?.LogTrace(message: "\"Disposing web socket test server raised operation cancel exception", exception: exception);
        }
        finally
        {
            this._httpListener.Stop();
            this._httpListener.Close();
            this._socketCancellationTokenSource.Dispose();
            this._mainCancellationTokenSource.Dispose();
        }
    }

    public void Dispose()
    {
        this.DisposeAsync().AsTask().GetAwaiter().GetResult();
    }
}
