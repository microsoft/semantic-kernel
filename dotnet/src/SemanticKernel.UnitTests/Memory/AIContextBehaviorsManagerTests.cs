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
/// Contains tests for the <see cref="AIContextBehaviorsManager"/> class.
/// </summary>
public class AIContextBehaviorsManagerTests
{
    [Fact]
    public void ConstructorShouldInitializeEmptyPartsList()
    {
        // Act
        var manager = new AIContextBehaviorsManager();

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
        var manager = new AIContextBehaviorsManager(new[] { mockPart.Object });

        // Assert
        Assert.Single(manager.Behaviors);
        Assert.Contains(mockPart.Object, manager.Behaviors);
    }

    [Fact]
    public void AddShouldRegisterNewPart()
    {
        // Arrange
        var manager = new AIContextBehaviorsManager();
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

        var manager = new AIContextBehaviorsManager();

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
        var manager = new AIContextBehaviorsManager();
        var mockPart = new Mock<AIContextBehavior>();
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
        var manager = new AIContextBehaviorsManager();
        var mockPart = new Mock<AIContextBehavior>();
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
        var manager = new AIContextBehaviorsManager();
        var mockPart = new Mock<AIContextBehavior>();
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
        var manager = new AIContextBehaviorsManager();
        var mockPart1 = new Mock<AIContextBehavior>();
        var mockPart2 = new Mock<AIContextBehavior>();
        mockPart1.Setup(x => x.OnModelInvokeAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                      .ReturnsAsync(new AIContextAdditions { AdditionalInstructions = "Context1" });
        mockPart2.Setup(x => x.OnModelInvokeAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                      .ReturnsAsync(new AIContextAdditions { AdditionalInstructions = "Context2" });
        manager.Add(mockPart1.Object);
        manager.Add(mockPart2.Object);

        var messages = new List<ChatMessage>();

        // Act
        var result = await manager.OnModelInvokeAsync(messages);

        // Assert
        Assert.Equal("Context1\nContext2", result.AdditionalInstructions);
    }

    [Fact]
    public async Task OnSuspendAsyncShouldCallOnSuspendOnAllParts()
    {
        // Arrange
        var manager = new AIContextBehaviorsManager();
        var mockPart = new Mock<AIContextBehavior>();
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
        var manager = new AIContextBehaviorsManager();
        var mockPart = new Mock<AIContextBehavior>();
        manager.Add(mockPart.Object);

        // Act
        await manager.OnResumeAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.OnResumeAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }
}
