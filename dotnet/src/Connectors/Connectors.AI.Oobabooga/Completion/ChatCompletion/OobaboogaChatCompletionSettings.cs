// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.WebSockets;
using System.Threading;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

/// <summary>
/// Settings for <see cref="OobaboogaChatCompletion"/>. It controls how oobabooga completion requests are made. Some parameters control the endpoint to which requests are sent, others control the behavior of the requests themselves. In particular, oobabooga offers a streaming API through websockets, and this class controls how websockets are managed for optimal resources management.
/// </summary>
public class OobaboogaChatCompletionSettings : OobaboogaCompletionSettings<OobaboogaChatCompletionParameters>
{
    private const string ChatBlockingUriPath = "/api/v1/chat";
    private const string ChatStreamingUriPath = "/api/v1/chat-stream";

    public OobaboogaChatCompletionSettings(Uri? endpoint = default,
        int blockingPort = 5000,
        int streamingPort = 5005,
        SemaphoreSlim? concurrentSemaphore = null,
        bool useWebSocketsPooling = true,
        CancellationToken? webSocketsCleanUpCancellationToken = default,
        int keepAliveWebSocketsDuration = 100,
        Func<ClientWebSocket>? webSocketFactory = null,
        HttpClient? httpClient = null,
        ILogger? logger = null) : base(endpoint, blockingPort, streamingPort, concurrentSemaphore, useWebSocketsPooling, webSocketsCleanUpCancellationToken, keepAliveWebSocketsDuration, webSocketFactory, httpClient, logger, ChatBlockingUriPath, ChatStreamingUriPath)
    {
    }
}
