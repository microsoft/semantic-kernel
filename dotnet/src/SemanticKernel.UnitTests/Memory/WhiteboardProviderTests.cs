// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

public class WhiteboardProviderTests
{
    private readonly Mock<IChatClient> _mockChatClient;
    private readonly Mock<ILogger<WhiteboardProvider>> _loggerMock;
    private readonly Mock<ILoggerFactory> _loggerFactoryMock;

    public WhiteboardProviderTests()
    {
        this._mockChatClient = new Mock<IChatClient>();
        this._loggerMock = new();
        this._loggerFactoryMock = new();

        this._loggerFactoryMock
            .Setup(f => f.CreateLogger(It.IsAny<string>()))
            .Returns(this._loggerMock.Object);
        this._loggerFactoryMock
            .Setup(f => f.CreateLogger(typeof(WhiteboardProvider).FullName!))
            .Returns(this._loggerMock.Object);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ShouldInvokeAIAndReturnWhiteboardMessagesInContextAsync(bool withLogging)
    {
        // Arrange
        var sut = withLogging
            ? new WhiteboardProvider(this._mockChatClient.Object, this._loggerFactoryMock.Object)
            : new WhiteboardProvider(this._mockChatClient.Object);

        var chatMessage = new ChatMessage(ChatRole.User, "I want to create a presentation");

        this._mockChatClient
            .Setup(service => service.GetResponseAsync(
                It.IsAny<IEnumerable<ChatMessage>>(),
                It.IsAny<ChatOptions?>(),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ChatResponse(new ChatMessage(ChatRole.Assistant, """{"newWhiteboard":["REQUIREMENT - User wants to create a presentation."]}""")));

        // Act
        await sut.MessageAddingAsync(null, chatMessage);

        // Assert
        this._mockChatClient.Verify(service => service.GetResponseAsync(
            It.Is<IEnumerable<ChatMessage>>(x => x.Count() == 1 && x.First().Text.Contains("I want to create a presentation")),
            It.IsAny<ChatOptions?>(),
            It.IsAny<CancellationToken>()), Times.Once);

        await sut.WhenProcessingCompleteAsync();
        var actualContext = await sut.ModelInvokingAsync([chatMessage]);
        Assert.Contains("REQUIREMENT - User wants to create a presentation", actualContext.Instructions);

        if (withLogging)
        {
            this._loggerMock.Verify(
                l => l.Log(
                    LogLevel.Trace,
                    It.IsAny<EventId>(),
                    It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains("WhiteboardBehavior: Updated whiteboard.\nInputMessages:\n[{\"Role\":\"user\",\"Text\":\"I want to create a presentation\"}]\nCurrentWhiteboard:\n[]\nNew Whiteboard:\n{\"newWhiteboard\":[\"REQUIREMENT - User wants to create a presentation.\"]}")),
                    It.IsAny<Exception?>(),
                    It.IsAny<Func<It.IsAnyType, Exception?, string>>()),
                Times.AtLeastOnce);

            this._loggerMock.Verify(
                l => l.Log(
                    LogLevel.Information,
                    It.IsAny<EventId>(),
                    It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains("WhiteboardBehavior: Whiteboard contains 1 messages")),
                    It.IsAny<Exception?>(),
                    It.IsAny<Func<It.IsAnyType, Exception?, string>>()),
                Times.AtLeastOnce);

            this._loggerMock.Verify(
                l => l.Log(
                    LogLevel.Trace,
                    It.IsAny<EventId>(),
                    It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains("WhiteboardBehavior: Output context instructions:\n## Whiteboard\nThe following list of messages are currently on the whiteboard:\n0 REQUIREMENT - User wants to create a presentation.")),
                    It.IsAny<Exception?>(),
                    It.IsAny<Func<It.IsAnyType, Exception?, string>>()),
                Times.AtLeastOnce);
        }
    }
}
