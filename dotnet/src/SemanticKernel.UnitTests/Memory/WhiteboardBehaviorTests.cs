// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

public class WhiteboardBehaviorTests
{
    private readonly Mock<IChatClient> _mockChatClient;

    public WhiteboardBehaviorTests()
    {
        this._mockChatClient = new Mock<IChatClient>();
    }

    [Fact]
    public async Task ShouldInvokeAIAndReturnWhiteboardMessagesInContextAsync()
    {
        // Arrange
        var sut = new WhiteboardBehavior(this._mockChatClient.Object);
        var chatMessage = new ChatMessage(ChatRole.User, "I want to create a presentation");

        this._mockChatClient
            .Setup(service => service.GetResponseAsync(
                It.IsAny<IEnumerable<ChatMessage>>(),
                It.IsAny<ChatOptions?>(),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ChatResponse(new ChatMessage(ChatRole.Assistant, """{"newWhiteboard":["REQUIREMENT - User wants to create a presentation."]}""")));

        // Act
        await sut.OnNewMessageAsync(null, chatMessage);

        // Assert
        this._mockChatClient.Verify(service => service.GetResponseAsync(
            It.Is<IEnumerable<ChatMessage>>(x => x.Count() == 1 && x.First().Text.Contains("I want to create a presentation")),
            It.IsAny<ChatOptions?>(),
            It.IsAny<CancellationToken>()), Times.Once);

        await sut.WhenProcessingCompleteAsync();
        var actualContext = await sut.OnModelInvokeAsync([chatMessage]);
        Assert.Contains("REQUIREMENT - User wants to create a presentation", actualContext.AdditionalInstructions);
    }
}
