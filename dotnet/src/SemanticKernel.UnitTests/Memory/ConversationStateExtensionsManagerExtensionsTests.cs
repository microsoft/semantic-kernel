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
/// Tests for the ConversationStateExtensionsManagerExtensions class.
/// </summary>
public class ConversationStateExtensionsManagerExtensionsTests
{
    [Fact]
    public async Task OnNewMessageShouldConvertMessageAndInvokeRegisteredExtensionsAsync()
    {
        // Arrange
        var manager = new ConversationStateExtensionsManager();
        var extensionMock = new Mock<ConversationStateExtension>();
        manager.Add(extensionMock.Object);

        var newMessage = new ChatMessageContent(AuthorRole.User, "Test Message");

        // Act
        await manager.OnNewMessageAsync(newMessage);

        // Assert
        extensionMock.Verify(x => x.OnNewMessageAsync(It.Is<ChatMessage>(m => m.Text == "Test Message" && m.Role == ChatRole.User), It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnAIInvocationShouldConvertMessagesInvokeRegisteredExtensionsAsync()
    {
        // Arrange
        var manager = new ConversationStateExtensionsManager();
        var extensionMock = new Mock<ConversationStateExtension>();
        manager.Add(extensionMock.Object);

        var messages = new List<ChatMessageContent>
        {
            new(AuthorRole.User, "Message 1"),
            new(AuthorRole.Assistant, "Message 2")
        };

        extensionMock
            .Setup(x => x.OnAIInvocationAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync("Combined Context");

        // Act
        var result = await manager.OnAIInvocationAsync(messages);

        // Assert
        Assert.Equal("Combined Context", result);
        extensionMock.Verify(x => x.OnAIInvocationAsync(It.Is<ICollection<ChatMessage>>(m => m.Count == 2), It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public void RegisterPluginsShouldConvertAIFunctionsAndRegisterAsPlugins()
    {
        // Arrange
        var kernel = new Kernel();
        var manager = new ConversationStateExtensionsManager();
        var extensionMock = new Mock<ConversationStateExtension>();
        var aiFunctionMock = AIFunctionFactory.Create(() => "Hello", "TestFunction");
        extensionMock
            .Setup(x => x.AIFunctions)
            .Returns(new List<AIFunction> { aiFunctionMock });
        manager.Add(extensionMock.Object);

        // Act
        manager.RegisterPlugins(kernel);

        // Assert
        var registeredFunction = kernel.Plugins.GetFunction("Tools", aiFunctionMock.Name);
        Assert.NotNull(registeredFunction);
    }
}
