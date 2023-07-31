// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.TextCompletion;

namespace SemanticKernel.Connectors.UnitTests.Oobabooga;

internal abstract class OobaboogaWebSocketTestServerBase : WebSocketTestServer
{
    public OobaboogaWebSocketTestServerBase(string url, Func<string, List<string>> stringHandler, ILogger? logger = null)
        : base(url, logger: logger)
    {
        this.ArraySegmentHandler = bytes => this.HandleRequest(bytes, stringHandler);
    }

    private List<ArraySegment<byte>> HandleRequest(ArraySegment<byte> request, Func<string, List<string>> stringHandler)
    {
        var requestString = Encoding.UTF8.GetString(request.ToArray());
        var requestObj = JsonSerializer.Deserialize<CompletionRequest>(requestString);

        var responseList = stringHandler(requestObj?.Prompt ?? string.Empty);

        var responseSegments = new List<ArraySegment<byte>>();
        int messageNum = 0;
        foreach (var responseChunk in responseList)
        {
            CompletionStreamingResponseBase responseObj = this.GetCompletionStreamingResponse(messageNum, responseChunk, responseList);

            var responseJson = JsonSerializer.Serialize(responseObj, responseObj.GetType());
            var responseBytes = Encoding.UTF8.GetBytes(responseJson);
            responseSegments.Add(new ArraySegment<byte>(responseBytes));

            messageNum++;
        }

        var streamEndObj = new TextCompletionStreamingResponse
        {
            Event = "stream_end",
            MessageNum = messageNum
        };

        var streamEndJson = JsonSerializer.Serialize(streamEndObj);
        var streamEndBytes = Encoding.UTF8.GetBytes(streamEndJson);
        responseSegments.Add(new ArraySegment<byte>(streamEndBytes));

        return responseSegments;
    }

    protected abstract CompletionStreamingResponseBase GetCompletionStreamingResponse(int messageNum, string responseChunk, List<string> responseList);
}
