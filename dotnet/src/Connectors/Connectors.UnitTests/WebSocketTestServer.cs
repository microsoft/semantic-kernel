// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.WebSockets;
using System.Threading;
using System.Threading.Tasks;

namespace SemanticKernel.Connectors.UnitTests;

internal class WebSocketTestServer : IDisposable
{
    private readonly HttpListener _httpListener;
    private Func<ArraySegment<byte>, List<ArraySegment<byte>>> _arraySegmentHandler;
    private readonly CancellationTokenSource _cts;
    private readonly ConcurrentDictionary<Guid, ConcurrentQueue<byte[]>> _requestContentQueues;
    private readonly ConcurrentBag<Task> _runningTasks = new();

    public TimeSpan RequestProcessingDelay { get; set; } = TimeSpan.Zero;

    public ConcurrentDictionary<Guid, byte[]> RequestContents
    {
        get
        {
            return new ConcurrentDictionary<Guid, byte[]>(
                this._requestContentQueues
                    .ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList().SelectMany(bytes => bytes).ToArray()));
        }
    }

    public WebSocketTestServer(string url, Func<ArraySegment<byte>, List<ArraySegment<byte>>> arraySegmentHandler)
    {
        this._httpListener = new HttpListener();
        this._httpListener.Prefixes.Add(url);
        this._httpListener.Start();
        this._arraySegmentHandler = arraySegmentHandler;
        this._cts = new CancellationTokenSource();
        this._requestContentQueues = new ConcurrentDictionary<Guid, ConcurrentQueue<byte[]>>();
        Task.Run((Func<Task>)this.HandleRequestsAsync, this._cts.Token);
    }

    private async Task HandleRequestsAsync()
    {
        while (!this._cts.IsCancellationRequested)
        {
            var context = await this._httpListener.GetContextAsync().ConfigureAwait(false);

            if (context.Request.IsWebSocketRequest)
            {
                this._runningTasks.Add(this.HandleSingleWebSocketRequestAsync(context));
            }
        }

        await Task.WhenAll(this._runningTasks).ConfigureAwait(false);
    }

    private async Task HandleSingleWebSocketRequestAsync(HttpListenerContext context)
    {
        var socketContext = await context.AcceptWebSocketAsync(null);
        var buffer = new byte[1024];
        var closeRequested = false;

        Guid requestId = Guid.NewGuid();
        this._requestContentQueues[requestId] = new ConcurrentQueue<byte[]>();
        try
        {
            while (!this._cts.IsCancellationRequested && !closeRequested)
            {
                if (socketContext.WebSocket.State != WebSocketState.Open)
                {
                    break;
                }

                WebSocketReceiveResult result;

                result = await socketContext.WebSocket.ReceiveAsync(new ArraySegment<byte>(buffer), this._cts.Token).ConfigureAwait(false);
                if (result.MessageType == WebSocketMessageType.Close)
                {
                    closeRequested = true;
                    // Send back a close frame
                    await socketContext.WebSocket.CloseOutputAsync(WebSocketCloseStatus.NormalClosure, "Closing without waiting for acknowledgment", this._cts.Token).ConfigureAwait(false);

                    break;
                }

                var receivedBytes = new ArraySegment<byte>(buffer, 0, result.Count).ToArray();
                this._requestContentQueues[requestId].Enqueue(receivedBytes);

                if (result.EndOfMessage)
                {
                    var responseSegments = this._arraySegmentHandler(new ArraySegment<byte>(buffer, 0, result.Count));

                    if (this.RequestProcessingDelay.Ticks > 0)
                    {
                        await Task.Delay(this.RequestProcessingDelay).ConfigureAwait(false);
                    }

                    foreach (var segment in responseSegments)
                    {
                        await socketContext.WebSocket.SendAsync(segment, WebSocketMessageType.Text, true, this._cts.Token).ConfigureAwait(false);
                    }
                }
            }

            if (socketContext.WebSocket.State == WebSocketState.Open)
            {
                await socketContext.WebSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing waiting for acknowledgement", CancellationToken.None).ConfigureAwait(false);
            }
            else if (socketContext.WebSocket.State == WebSocketState.CloseReceived)
            {
                await socketContext.WebSocket.CloseOutputAsync(WebSocketCloseStatus.NormalClosure, "Closing without waiting for acknowledgment", CancellationToken.None).ConfigureAwait(false);
            }
        }
        catch (OperationCanceledException)
        {
        }
        catch (WebSocketException)
        {
        }
        finally
        {
            socketContext.WebSocket.Dispose();
        }
    }

    public async ValueTask DisposeAsync()
    {
        this._cts.Cancel();
        try
        {
            await Task.WhenAll(this._runningTasks).ConfigureAwait(false);
        }
        finally
        {
            this._httpListener.Stop();
            this._httpListener.Close();
            this._cts.Dispose();
        }
    }

    public void Dispose()
    {
        this.DisposeAsync().AsTask().GetAwaiter().GetResult();
    }
}
