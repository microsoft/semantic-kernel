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
            var context = await this._httpListener.GetContextAsync();

            if (context.Request.IsWebSocketRequest)
            {
                var socketContext = await context.AcceptWebSocketAsync(null);
                var buffer = new byte[1024];
                var closeRequested = false;

                Guid requestId = Guid.NewGuid();
                this._requestContentQueues[requestId] = new ConcurrentQueue<byte[]>();

                while (!closeRequested)
                {
                    var result = await socketContext.WebSocket.ReceiveAsync(new ArraySegment<byte>(buffer), this._cts.Token);

                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        closeRequested = true;
                        break;
                    }

                    var receivedBytes = new ArraySegment<byte>(buffer, 0, result.Count).ToArray();
                    this._requestContentQueues[requestId].Enqueue(receivedBytes);

                    if (result.EndOfMessage)
                    {
                        var responseSegments = this._arraySegmentHandler(new ArraySegment<byte>(buffer, 0, result.Count));

                        foreach (var segment in responseSegments)
                        {
                            await socketContext.WebSocket.SendAsync(segment, WebSocketMessageType.Text, true, this._cts.Token);
                        }
                    }
                }

                await socketContext.WebSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", this._cts.Token);
            }
        }
    }

    public void Dispose()
    {
        this._cts.Cancel();
        this._cts.Dispose();
        this._httpListener.Stop();
        this._httpListener.Close();
    }
}
