﻿// Copyright (c) Microsoft. All rights reserved.

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
/// Tests for the ConversationStatePartsManagerExtensions class.
/// </summary>
public class ConversationStatePartsManagerExtensionsTests
{
    [Fact]
    public async Task OnNewMessageShouldConvertMessageAndInvokeRegisteredPartsAsync()
    {
        // Arrange
        var manager = new ConversationStatePartsManager();
        var partMock = new Mock<ConversationStatePart>();
        manager.Add(partMock.Object);

        var newMessage = new ChatMessageContent(AuthorRole.User, "Test Message");

        // Act
        await manager.OnNewMessageAsync("test-thread-id", newMessage);

        // Assert
        partMock.Verify(x => x.OnNewMessageAsync("test-thread-id", It.Is<ChatMessage>(m => m.Text == "Test Message" && m.Role == ChatRole.User), It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnAIInvocationShouldConvertMessagesInvokeRegisteredPartsAsync()
    {
        // Arrange
        var manager = new ConversationStatePartsManager();
        var partMock = new Mock<ConversationStatePart>();
        manager.Add(partMock.Object);

        var messages = new List<ChatMessageContent>
        {
            new(AuthorRole.User, "Message 1"),
            new(AuthorRole.Assistant, "Message 2")
        };

        partMock
            .Setup(x => x.OnModelInvokeAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync("Combined Context");

        // Act
        var result = await manager.OnModelInvokeAsync(messages);

        // Assert
        Assert.Equal("Combined Context", result);
        partMock.Verify(x => x.OnModelInvokeAsync(It.Is<ICollection<ChatMessage>>(m => m.Count == 2), It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public void RegisterPluginsShouldConvertAIFunctionsAndRegisterAsPlugins()
    {
        // Arrange
        var kernel = new Kernel();
        var manager = new ConversationStatePartsManager();
        var partMock = new Mock<ConversationStatePart>();
        var aiFunctionMock = AIFunctionFactory.Create(() => "Hello", "TestFunction");
        partMock
            .Setup(x => x.AIFunctions)
            .Returns(new List<AIFunction> { aiFunctionMock });
        manager.Add(partMock.Object);

        // Act
        manager.RegisterPlugins(kernel);

        // Assert
        var registeredFunction = kernel.Plugins.GetFunction("Tools", aiFunctionMock.Name);
        Assert.NotNull(registeredFunction);
    }
}
