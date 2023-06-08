// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Net.WebSockets;
using System.Threading;
using System.Threading.Tasks;

namespace SemanticKernel.Connectors.UnitTests;

internal sealed class WebSocketTestServer : IDisposable
{
    private readonly HttpListener _httpListener;
    private readonly Func<ArraySegment<byte>, ArraySegment<byte>> _handleRequest;
    private readonly CancellationTokenSource _cts;
    private readonly List<byte> _requestContents;

    public byte[] RequestContent => this._requestContents.ToArray();

    public WebSocketTestServer(string url, Func<ArraySegment<byte>, ArraySegment<byte>> handleRequest)
    {
        this._httpListener = new HttpListener();
        this._httpListener.Prefixes.Add(url);
        this._httpListener.Start();
        this._handleRequest = handleRequest;
        this._cts = new CancellationTokenSource();
        this._requestContents = new List<byte>();
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
                var result = await socketContext.WebSocket.ReceiveAsync(new ArraySegment<byte>(buffer), this._cts.Token);

                var receivedBytes = new ArraySegment<byte>(buffer, 0, result.Count).ToArray();
                this._requestContents.AddRange(receivedBytes);

                var response = this._handleRequest(new ArraySegment<byte>(buffer, 0, result.Count));
                await socketContext.WebSocket.SendAsync(response, WebSocketMessageType.Text, true, this._cts.Token);
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
