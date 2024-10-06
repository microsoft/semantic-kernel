// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Text;
using Xunit;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

namespace SemanticKernel.UnitTests.Utilities;

public sealed class SseJsonParserTests
{
    public const string SampleSseData1 =
        """
        event: message_start
        data: {"type": "message_start", "message": {"id": "msg_1nZdL29xx5MUA1yADyHTEsnR8uuvGzszyY", "type": "message", "role": "assistant", "content": [], "model": "claude-3-opus-20240229", "stop_reason": null, "stop_sequence": null, "usage": {"input_tokens": 25, "output_tokens": 1}}}

        event: content_block_start
        data: {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}

        event: ping
        data: {"type": "ping"}

        event: content_block_delta
        data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hello"}}

        event: content_block_delta
        data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "!"}}

        event: content_block_stop
        data: {"type": "content_block_stop", "index": 0}

        event: message_delta
        data: {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence":null, "usage":{"output_tokens": 15}}}

        event: message_stop
        data: {"type": "message_stop"}

        """;

    public const string SampleSseData2 =
        """
        event: userconnect
        data: {"username": "bobby", "time": "02:33:48"}

        event: usermessage
        data: {"username": "bobby", "time": "02:34:11", "text": "Hi everyone."}

        event: userdisconnect
        data: {"username": "bobby", "time": "02:34:23"}

        event: usermessage
        data: {"username": "sean", "time": "02:34:36", "text": "Bye, bobby."}
        """;

    public const string SampleSseData3 =
        """
        event: userconnect
        data: {"username": "bobby", "time": "02:33:48"}

        data: Here's a system message of some kind that will get used
        data: to accomplish some task.

        event: usermessage
        data: {"username": "bobby", "time": "02:34:11", "text": "Hi everyone."}
        """;

    public const string SampleSseData4 =
        """
        event: userconnect
        data: {"username": "bobby", "time": "02:33:48"}

        data: none

        event: usermessage
        data: {"username": "bobby", "time": "02:34:11", "text": "Hi everyone."}

        event: userdisconnect
        data: {"username": "bobby", "time": "02:34:23"}
        data:
        data
        id: 3

        data: [DONE]

        event: usermessage
        data: {"username": "sean", "time": "02:34:36", "text": "Bye, bobby."}

        """;

    [Theory]
    [InlineData(SampleSseData1)]
    [InlineData(SampleSseData2)]
    [InlineData(SampleSseData3)]
    [InlineData(SampleSseData4)]
    public async Task ItReturnsAnyDataAsync(string data)
    {
        // Arrange
        using var stream = new MemoryStream();
        WriteToStream(stream, data);

        // Act
        var result = await SseJsonParser.ParseAsync(stream,
                line => new SseData(line.EventName, line.FieldValue)
                , CancellationToken.None)
            .ToListAsync();

        // Assert
        Assert.NotEmpty(result);
    }

    [Fact]
    public async Task ItReturnsValidEventNamesAsync()
    {
        // Arrange
        using var stream = new MemoryStream();
        WriteToStream(stream, SampleSseData2);

        // Act
        var result = await SseJsonParser.ParseAsync(
                stream,
                line => new SseData(line.EventName, line.FieldValue),
                CancellationToken.None)
            .ToListAsync();

        // Assert
        Assert.Collection(result,
            item => Assert.Equal("userconnect", item.EventName),
            item => Assert.Equal("usermessage", item.EventName),
            item => Assert.Equal("userdisconnect", item.EventName),
            item => Assert.Equal("usermessage", item.EventName));
    }

    [Fact]
    public async Task ItReturnsAllParsedJsonsAsync()
    {
        // Arrange
        using var stream = new MemoryStream();
        WriteToStream(stream, SampleSseData1);

        // Act
        var result = await SseJsonParser.ParseAsync(
                stream,
                line =>
                {
                    var obj = JsonSerializer.Deserialize<object>(line.FieldValue.Span, JsonOptionsCache.ReadPermissive);
                    return new SseData(line.EventName, obj!);
                },
                CancellationToken.None)
            .ToListAsync();

        // Assert
        Assert.Equal(8, result.Count);
    }

    [Fact]
    public async Task ItReturnsValidParsedDataAsync()
    {
        // Arrange
        using var stream = new MemoryStream();
        WriteToStream(stream, SampleSseData3);

        // Act
        var result = await SseJsonParser.ParseAsync(stream,
                line =>
                {
                    if (line.EventName is null)
                    {
                        return null;
                    }

                    var userObject = JsonSerializer.Deserialize<UserObject>(line.FieldValue.Span, JsonOptionsCache.ReadPermissive);
                    return new SseData(line.EventName, userObject!);
                },
                CancellationToken.None)
            .ToListAsync();

        // Assert
        Assert.Collection(result,
            item =>
            {
                Assert.Equal("userconnect", item.EventName);
                var userObject = Assert.IsType<UserObject>(item.Data);
                Assert.Equal("bobby", userObject.Username);
                Assert.Equal(TimeSpan.Parse("02:33:48", formatProvider: new DateTimeFormatInfo()), userObject.Time);
                Assert.Null(userObject.Text);
            },
            item =>
            {
                Assert.Equal("usermessage", item.EventName);
                var userObject = Assert.IsType<UserObject>(item.Data);
                Assert.Equal("bobby", userObject.Username);
                Assert.Equal(TimeSpan.Parse("02:34:11", formatProvider: new DateTimeFormatInfo()), userObject.Time);
                Assert.Equal("Hi everyone.", userObject.Text);
            });
    }

    private static void WriteToStream(Stream stream, string input)
    {
        using var writer = new StreamWriter(stream, leaveOpen: true);
        writer.Write(input);
        writer.Flush();
        stream.Position = 0;
    }

    private sealed class UserObject
    {
        public string? Username { get; set; }
        public TimeSpan Time { get; set; }
        public string? Text { get; set; }
    }
}
