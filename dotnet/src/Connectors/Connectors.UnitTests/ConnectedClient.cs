// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.WebSockets;

namespace SemanticKernel.Connectors.UnitTests;

internal sealed class ConnectedClient
{
    public Guid Id { get; }
    public HttpListenerContext Context { get; }
    public WebSocket? Socket { get; private set; }

    public ConnectedClient(Guid id, HttpListenerContext context)
    {
        this.Id = id;
        this.Context = context;
    }

    public void SetSocket(WebSocket socket)
    {
        this.Socket = socket;
    }
}
