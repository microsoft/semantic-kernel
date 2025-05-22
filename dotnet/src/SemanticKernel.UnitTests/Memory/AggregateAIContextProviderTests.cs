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
/// Contains tests for the <see cref="AggregateAIContextProvider"/> class.
/// </summary>
public class AggregateAIContextProviderTests
{
    [Fact]
    public void ConstructorShouldInitializeEmptyPartsList()
    {
        // Act
        var sut = new AggregateAIContextProvider();

        // Assert
        Assert.NotNull(sut.Providers);
        Assert.Empty(sut.Providers);
    }

    [Fact]
    public void ConstructorShouldInitializeWithProvidedParts()
    {
        // Arrange
        var mockPart = new Mock<AIContextProvider>();

        // Act
        var sut = new AggregateAIContextProvider(new[] { mockPart.Object });

        // Assert
        Assert.Single(sut.Providers);
        Assert.Contains(mockPart.Object, sut.Providers);
    }

    [Fact]
    public void AddShouldRegisterNewPart()
    {
        // Arrange
        var sut = new AggregateAIContextProvider();
        var mockPart = new Mock<AIContextProvider>();

        // Act
        sut.Add(mockPart.Object);

        // Assert
        Assert.Single(sut.Providers);
        Assert.Contains(mockPart.Object, sut.Providers);
    }

    [Fact]
    public void AddFromServiceProviderShouldRegisterPartsFromServiceProvider()
    {
        // Arrange
        var serviceCollection = new ServiceCollection();
        var mockPart = new Mock<AIContextProvider>();
        serviceCollection.AddSingleton(mockPart.Object);
        var serviceProvider = serviceCollection.BuildServiceProvider();

        var sut = new AggregateAIContextProvider();

        // Act
        sut.AddFromServiceProvider(serviceProvider);

        // Assert
        Assert.Single(sut.Providers);
        Assert.Contains(mockPart.Object, sut.Providers);
    }

    [Fact]
    public async Task OnThreadCreatedAsyncShouldCallOnThreadCreatedOnAllParts()
    {
        // Arrange
        var sut = new AggregateAIContextProvider();
        var mockPart = new Mock<AIContextProvider>();
        sut.Add(mockPart.Object);

        // Act
        await sut.ConversationCreatedAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.ConversationCreatedAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnThreadDeleteAsyncShouldCallOnThreadDeleteOnAllParts()
    {
        // Arrange
        var sut = new AggregateAIContextProvider();
        var mockPart = new Mock<AIContextProvider>();
        sut.Add(mockPart.Object);

        // Act
        await sut.ConversationDeletingAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.ConversationDeletingAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnNewMessageAsyncShouldCallOnNewMessageOnAllParts()
    {
        // Arrange
        var sut = new AggregateAIContextProvider();
        var mockPart = new Mock<AIContextProvider>();
        var message = new ChatMessage(ChatRole.User, "Hello");
        sut.Add(mockPart.Object);

        // Act
        await sut.MessageAddingAsync("test-thread-id", message);

        // Assert
        mockPart.Verify(x => x.MessageAddingAsync("test-thread-id", message, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnAIInvocationAsyncShouldAggregateContextsFromAllParts()
    {
        // Arrange
        var sut = new AggregateAIContextProvider();
        var mockPart1 = new Mock<AIContextProvider>();
        var mockPart2 = new Mock<AIContextProvider>();
        mockPart1.Setup(x => x.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                      .ReturnsAsync(new AIContext { Instructions = "Context1" });
        mockPart2.Setup(x => x.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                      .ReturnsAsync(new AIContext { Instructions = "Context2" });
        sut.Add(mockPart1.Object);
        sut.Add(mockPart2.Object);

        var messages = new List<ChatMessage>();

        // Act
        var result = await sut.ModelInvokingAsync(messages);

        // Assert
        Assert.Equal("Context1\nContext2", result.Instructions);
    }

    [Fact]
    public async Task OnSuspendAsyncShouldCallOnSuspendOnAllParts()
    {
        // Arrange
        var sut = new AggregateAIContextProvider();
        var mockPart = new Mock<AIContextProvider>();
        sut.Add(mockPart.Object);

        // Act
        await sut.SuspendingAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.SuspendingAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnResumeAsyncShouldCallOnResumeOnAllParts()
    {
        // Arrange
        var sut = new AggregateAIContextProvider();
        var mockPart = new Mock<AIContextProvider>();
        sut.Add(mockPart.Object);

        // Act
        await sut.ResumingAsync("test-thread-id");

        // Assert
        mockPart.Verify(x => x.ResumingAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }
}
