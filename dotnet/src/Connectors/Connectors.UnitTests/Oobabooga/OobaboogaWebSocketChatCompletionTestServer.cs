// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

namespace SemanticKernel.Connectors.UnitTests.Oobabooga;

/// <summary>
/// Represents a WebSocket test server specifically designed for the Oobabooga text completion service.
/// It inherits from the base WebSocketTestServer class and handles Oobabooga-specific request and response classes.
/// The server accepts WebSocket connections, receives requests, and generates responses based on the Oobabooga text completion logic.
/// The OobaboogaWebSocketTestServer class uses a delegate to handle the request and response logic, allowing customization of the behavior.
/// </summary>
internal sealed class OobaboogaWebSocketChatCompletionTestServer : OobaboogaWebSocketTestServerBase
{
    public OobaboogaWebSocketChatCompletionTestServer(string url, Func<string, List<string>> stringHandler, ILogger? logger = null)
        : base(url, stringHandler, logger)
    {
    }

    protected override CompletionStreamingResponseBase GetCompletionStreamingResponse(int messageNum, string responseChunk, List<string> responseList)
    {
        var strMessage = responseList.Take(messageNum + 1).Aggregate((s1, s2) => s1 + s2);
        var responseObj = new ChatCompletionStreamingResponse
        {
            Event = "text_stream",
            MessageNum = messageNum,
            History = new ChatHistory { Internal = new() { new List<string> { strMessage } }, Visible = new() { new List<string> { strMessage } } }
        };
        return responseObj;
    }
}
