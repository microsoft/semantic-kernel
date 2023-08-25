// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.WebSockets;
using System.Threading;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.TextCompletion;

/// <summary>
/// Settings for <see cref="OobaboogaTextCompletion"/>. It controls how oobabooga completion requests are made. Some parameters control the endpoint to which requests are sent, others control the behavior of the requests themselves. In particular, oobabooga offers a streaming API through websockets, and this class controls how websockets are managed for optimal resources management.
/// </summary>
public class OobaboogaTextCompletionSettings : OobaboogaCompletionSettings<OobaboogaCompletionParameters>
{
    /// <summary>
    ///  Initializes a new instance of the <see cref="OobaboogaTextCompletionSettings"/> class, which controls how oobabooga completion requests are made.
    /// </summary>
    /// <param name="endpoint">The service API endpoint to which requests should be sent.</param>
    /// <param name="blockingPort">The port used for handling blocking requests. Default value is 5000</param>
    /// <param name="streamingPort">The port used for handling streaming requests. Default value is 5005</param>
    /// <param name="concurrentSemaphore">You can optionally set a hard limit on the max number of concurrent calls to the either of the completion methods by providing a <see cref="SemaphoreSlim"/>. Calls in excess will wait for existing consumers to release the semaphore</param>
    /// <param name="useWebSocketsPooling">If true, websocket clients will be recycled in a reusable pool as long as concurrent calls are detected</param>
    /// <param name="webSocketsCleanUpCancellationToken">if websocket pooling is enabled, you can provide an optional CancellationToken to properly dispose of the clean up tasks when disposing of the connector</param>
    /// <param name="keepAliveWebSocketsDuration">When pooling is enabled, pooled websockets are flushed on a regular basis when no more connections are made. This is the time to keep them in pool before flushing</param>
    /// <param name="webSocketFactory">The WebSocket factory used for making streaming API requests. Note that only when pooling is enabled will websocket be recycled and reused for the specified duration. Otherwise, a new websocket is created for each call and closed and disposed afterwards, to prevent data corruption from concurrent calls.</param>
    /// <param name="httpClient">Optional. The HTTP client used for making blocking API requests. If not specified, a default client will be used.</param>
    /// <param name="logger">Application logger</param>
    public OobaboogaTextCompletionSettings(Uri? endpoint = default,
        int blockingPort = 5000,
        int streamingPort = 5005,
        SemaphoreSlim? concurrentSemaphore = null,
        bool useWebSocketsPooling = true,
        CancellationToken? webSocketsCleanUpCancellationToken = default,
        int keepAliveWebSocketsDuration = 100,
        Func<ClientWebSocket>? webSocketFactory = null,
        HttpClient? httpClient = null,
        ILogger? logger = null) : base(endpoint, blockingPort, streamingPort, concurrentSemaphore, useWebSocketsPooling, webSocketsCleanUpCancellationToken, keepAliveWebSocketsDuration, webSocketFactory, httpClient, logger)
    {
    }
}
