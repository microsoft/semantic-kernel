// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

namespace SemanticKernel.Connectors.UnitTests.Oobabooga;

internal sealed class OobaboogaWebSocketTestServer : WebSocketTestServer
{
    public OobaboogaWebSocketTestServer(string url, Func<string, List<string>> stringHandler)
        : base(url, bytes => HandleRequest(bytes, stringHandler))
    {
    }

    private static List<ArraySegment<byte>> HandleRequest(ArraySegment<byte> request, Func<string, List<string>> stringHandler)
    {
        var requestString = Encoding.UTF8.GetString(request.ToArray());
        var requestObj = JsonSerializer.Deserialize<TextCompletionRequest>(requestString);

        var responseList = stringHandler(requestObj?.Prompt ?? string.Empty);

        var responseSegments = new List<ArraySegment<byte>>();
        int messageNum = 0;
        foreach (var responseChunk in responseList)
        {
            var responseObj = new TextCompletionStreamingResponse
            {
                Event = "text_stream",
                MessageNum = messageNum,
                Text = responseChunk
            };

            var responseJson = JsonSerializer.Serialize(responseObj);
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
}
