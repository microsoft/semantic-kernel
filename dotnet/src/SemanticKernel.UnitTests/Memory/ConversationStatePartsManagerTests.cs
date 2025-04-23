// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

/// <summary>
/// Contains tests for the <see cref="ConversationStatePartsManager"/> class.
/// </summary>
public class ConversationStatePartsManagerTests
{
    [Fact]
    public void ConstructorShouldInitializeEmptyPartsList()
    {
        // Act
        var manager = new ConversationStatePartsManager();

        // Assert
        Assert.NotNull(manager.Parts);
        Assert.Empty(manager.Parts);
    }

    [Fact]
    public void ConstructorShouldInitializeWithProvidedParts()
    {
        // Arrange
        var mockPart = new Mock<ConversationStatePart>();

        // Act
        var manager = new ConversationStatePartsManager(new[] { mockPart.Object });

        // Assert
        Assert.Single(manager.Parts);
        Assert.Contains(mockPart.Object, manager.Parts);
    }

    [Fact]
    public void AddShouldRegisterNewPart()
    {
        // Arrange
        var manager = new ConversationStatePartsManager();
        var mockPart = new Mock<ConversationStatePart>();

        // Act
        manager.Add(mockPart.Object);

        // Assert
        Assert.Single(manager.Parts);
        Assert.Contains(mockPart.Object, manager.Parts);
    }

    [Fact]
    public void AddFromServiceProviderShouldRegisterPartsFromServiceProvider()
    {
        // Arrange
        var serviceCollection = new ServiceCollection();
        var mockPart = new Mock<ConversationStatePart>();
        serviceCollection.AddSingleton(mockPart.Object);
        var serviceProvider = serviceCollection.BuildServiceProvider();

        var manager = new ConversationStatePartsManager();

        // Act
        manager.AddFromServiceProvider(serviceProvider);

        // Assert
        Assert.Single(manager.Parts);
        Assert.Contains(mockPart.Object, manager.Parts);
    }

    [Fact]
    public async Task OnThreadCreatedAsyncShouldCallOnThreadCreatedOnAllParts()
    {
        // Arrange
        var manager = new ConversationStatePartsManager();
        var mockPart = new Mock<ConversationStatePart>();
        manager.Add(mockPart.Object);

        // Act
        await manager.OnThreadCreatedAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.OnThreadCreatedAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnThreadDeleteAsyncShouldCallOnThreadDeleteOnAllParts()
    {
        // Arrange
        var manager = new ConversationStatePartsManager();
        var mockPart = new Mock<ConversationStatePart>();
        manager.Add(mockPart.Object);

        // Act
        await manager.OnThreadDeleteAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.OnThreadDeleteAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnNewMessageAsyncShouldCallOnNewMessageOnAllParts()
    {
        // Arrange
        var manager = new ConversationStatePartsManager();
        var mockPart = new Mock<ConversationStatePart>();
        var message = new ChatMessage(ChatRole.User, "Hello");
        manager.Add(mockPart.Object);

        // Act
        await manager.OnNewMessageAsync("test-thread-id", message);

        // Assert
        mockPart.Verify(x => x.OnNewMessageAsync("test-thread-id", message, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnAIInvocationAsyncShouldAggregateContextsFromAllParts()
    {
        // Arrange
        var manager = new ConversationStatePartsManager();
        var mockPart1 = new Mock<ConversationStatePart>();
        var mockPart2 = new Mock<ConversationStatePart>();
        mockPart1.Setup(x => x.OnModelInvokeAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                      .ReturnsAsync("Context1");
        mockPart2.Setup(x => x.OnModelInvokeAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                      .ReturnsAsync("Context2");
        manager.Add(mockPart1.Object);
        manager.Add(mockPart2.Object);

        var messages = new List<ChatMessage>();

        // Act
        var result = await manager.OnModelInvokeAsync(messages);

        // Assert
        Assert.Equal("Context1\nContext2", result);
    }

    [Fact]
    public async Task OnSuspendAsyncShouldCallOnSuspendOnAllParts()
    {
        // Arrange
        var manager = new ConversationStatePartsManager();
        var mockPart = new Mock<ConversationStatePart>();
        manager.Add(mockPart.Object);

        // Act
        await manager.OnSuspendAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.OnSuspendAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnResumeAsyncShouldCallOnResumeOnAllParts()
    {
        // Arrange
        var manager = new ConversationStatePartsManager();
        var mockPart = new Mock<ConversationStatePart>();
        manager.Add(mockPart.Object);

        // Act
        await manager.OnResumeAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.OnResumeAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }
}
