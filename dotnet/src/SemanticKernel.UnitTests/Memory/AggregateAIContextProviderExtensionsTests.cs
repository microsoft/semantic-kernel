// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

/// <summary>
/// Tests for the AggregateAIContextProviderExtensions class.
/// </summary>
public class AggregateAIContextProviderExtensionsTests
{
    [Fact]
    public async Task OnNewMessageShouldConvertMessageAndInvokeRegisteredPartsAsync()
    {
        // Arrange
        var manager = new AggregateAIContextProvider();
        var partMock = new Mock<AIContextProvider>();
        manager.Add(partMock.Object);

        var newMessage = new ChatMessageContent(AuthorRole.User, "Test Message");

        // Act
        await manager.MessageAddingAsync("test-thread-id", newMessage);

        // Assert
        partMock.Verify(x => x.MessageAddingAsync("test-thread-id", It.Is<ChatMessage>(m => m.Text == "Test Message" && m.Role == ChatRole.User), It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnAIInvocationShouldConvertMessagesInvokeRegisteredPartsAsync()
    {
        // Arrange
        var manager = new AggregateAIContextProvider();
        var partMock = new Mock<AIContextProvider>();
        manager.Add(partMock.Object);

        var messages = new List<ChatMessageContent>
        {
            new(AuthorRole.User, "Message 1"),
            new(AuthorRole.Assistant, "Message 2")
        };

        partMock
            .Setup(x => x.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new AIContext { Instructions = "Combined Context" });

        // Act
        var result = await manager.ModelInvokingAsync(messages);

        // Assert
        Assert.Equal("Combined Context", result.Instructions);
        partMock.Verify(x => x.ModelInvokingAsync(It.Is<ICollection<ChatMessage>>(m => m.Count == 2), It.IsAny<CancellationToken>()), Times.Once);
    }
}
