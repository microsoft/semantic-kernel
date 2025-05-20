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
/// Contains tests for the <see cref="AggregateAIContextBehavior"/> class.
/// </summary>
public class AggregateAIContextBehaviorTests
{
    [Fact]
    public void ConstructorShouldInitializeEmptyPartsList()
    {
        // Act
        var manager = new AggregateAIContextBehavior();

        // Assert
        Assert.NotNull(manager.Behaviors);
        Assert.Empty(manager.Behaviors);
    }

    [Fact]
    public void ConstructorShouldInitializeWithProvidedParts()
    {
        // Arrange
        var mockPart = new Mock<AIContextBehavior>();

        // Act
        var manager = new AggregateAIContextBehavior(new[] { mockPart.Object });

        // Assert
        Assert.Single(manager.Behaviors);
        Assert.Contains(mockPart.Object, manager.Behaviors);
    }

    [Fact]
    public void AddShouldRegisterNewPart()
    {
        // Arrange
        var manager = new AggregateAIContextBehavior();
        var mockPart = new Mock<AIContextBehavior>();

        // Act
        manager.Add(mockPart.Object);

        // Assert
        Assert.Single(manager.Behaviors);
        Assert.Contains(mockPart.Object, manager.Behaviors);
    }

    [Fact]
    public void AddFromServiceProviderShouldRegisterPartsFromServiceProvider()
    {
        // Arrange
        var serviceCollection = new ServiceCollection();
        var mockPart = new Mock<AIContextBehavior>();
        serviceCollection.AddSingleton(mockPart.Object);
        var serviceProvider = serviceCollection.BuildServiceProvider();

        var manager = new AggregateAIContextBehavior();

        // Act
        manager.AddFromServiceProvider(serviceProvider);

        // Assert
        Assert.Single(manager.Behaviors);
        Assert.Contains(mockPart.Object, manager.Behaviors);
    }

    [Fact]
    public async Task OnThreadCreatedAsyncShouldCallOnThreadCreatedOnAllParts()
    {
        // Arrange
        var manager = new AggregateAIContextBehavior();
        var mockPart = new Mock<AIContextBehavior>();
        manager.Add(mockPart.Object);

        // Act
        await manager.ThreadCreatedAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.ThreadCreatedAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnThreadDeleteAsyncShouldCallOnThreadDeleteOnAllParts()
    {
        // Arrange
        var manager = new AggregateAIContextBehavior();
        var mockPart = new Mock<AIContextBehavior>();
        manager.Add(mockPart.Object);

        // Act
        await manager.ThreadDeletingAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.ThreadDeletingAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnNewMessageAsyncShouldCallOnNewMessageOnAllParts()
    {
        // Arrange
        var manager = new AggregateAIContextBehavior();
        var mockPart = new Mock<AIContextBehavior>();
        var message = new ChatMessage(ChatRole.User, "Hello");
        manager.Add(mockPart.Object);

        // Act
        await manager.MessageAddingAsync("test-thread-id", message);

        // Assert
        mockPart.Verify(x => x.MessageAddingAsync("test-thread-id", message, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnAIInvocationAsyncShouldAggregateContextsFromAllParts()
    {
        // Arrange
        var manager = new AggregateAIContextBehavior();
        var mockPart1 = new Mock<AIContextBehavior>();
        var mockPart2 = new Mock<AIContextBehavior>();
        mockPart1.Setup(x => x.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                      .ReturnsAsync(new AIContextPart { Instructions = "Context1" });
        mockPart2.Setup(x => x.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                      .ReturnsAsync(new AIContextPart { Instructions = "Context2" });
        manager.Add(mockPart1.Object);
        manager.Add(mockPart2.Object);

        var messages = new List<ChatMessage>();

        // Act
        var result = await manager.ModelInvokingAsync(messages);

        // Assert
        Assert.Equal("Context1\nContext2", result.Instructions);
    }

    [Fact]
    public async Task OnSuspendAsyncShouldCallOnSuspendOnAllParts()
    {
        // Arrange
        var manager = new AggregateAIContextBehavior();
        var mockPart = new Mock<AIContextBehavior>();
        manager.Add(mockPart.Object);

        // Act
        await manager.SuspendingAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.SuspendingAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnResumeAsyncShouldCallOnResumeOnAllParts()
    {
        // Arrange
        var manager = new AggregateAIContextBehavior();
        var mockPart = new Mock<AIContextBehavior>();
        manager.Add(mockPart.Object);

        // Act
        await manager.ResumingAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.ResumingAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }
}
