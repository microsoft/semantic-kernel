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
/// Contains tests for the <see cref="ConversationStateExtensionsManager"/> class.
/// </summary>
public class ConversationStateExtensionsManagerTests
{
    [Fact]
    public void ConstructorShouldInitializeEmptyExtensionsList()
    {
        // Act
        var manager = new ConversationStateExtensionsManager();

        // Assert
        Assert.NotNull(manager.Extensions);
        Assert.Empty(manager.Extensions);
    }

    [Fact]
    public void ConstructorShouldInitializeWithProvidedExtensions()
    {
        // Arrange
        var mockExtension = new Mock<ConversationStateExtension>();

        // Act
        var manager = new ConversationStateExtensionsManager(new[] { mockExtension.Object });

        // Assert
        Assert.Single(manager.Extensions);
        Assert.Contains(mockExtension.Object, manager.Extensions);
    }

    [Fact]
    public void AddShouldRegisterNewExtension()
    {
        // Arrange
        var manager = new ConversationStateExtensionsManager();
        var mockExtension = new Mock<ConversationStateExtension>();

        // Act
        manager.Add(mockExtension.Object);

        // Assert
        Assert.Single(manager.Extensions);
        Assert.Contains(mockExtension.Object, manager.Extensions);
    }

    [Fact]
    public void AddFromServiceProviderShouldRegisterExtensionsFromServiceProvider()
    {
        // Arrange
        var serviceCollection = new ServiceCollection();
        var mockExtension = new Mock<ConversationStateExtension>();
        serviceCollection.AddSingleton(mockExtension.Object);
        var serviceProvider = serviceCollection.BuildServiceProvider();

        var manager = new ConversationStateExtensionsManager();

        // Act
        manager.AddFromServiceProvider(serviceProvider);

        // Assert
        Assert.Single(manager.Extensions);
        Assert.Contains(mockExtension.Object, manager.Extensions);
    }

    [Fact]
    public async Task OnThreadCreatedAsyncShouldCallOnThreadCreatedOnAllExtensions()
    {
        // Arrange
        var manager = new ConversationStateExtensionsManager();
        var mockExtension = new Mock<ConversationStateExtension>();
        manager.Add(mockExtension.Object);

        // Act
        await manager.OnThreadCreatedAsync("test-thread-id");

        // Assert
        mockExtension.Verify(x => x.OnThreadCreatedAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnThreadDeleteAsyncShouldCallOnThreadDeleteOnAllExtensions()
    {
        // Arrange
        var manager = new ConversationStateExtensionsManager();
        var mockExtension = new Mock<ConversationStateExtension>();
        manager.Add(mockExtension.Object);

        // Act
        await manager.OnThreadDeleteAsync("test-thread-id");

        // Assert
        mockExtension.Verify(x => x.OnThreadDeleteAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnNewMessageAsyncShouldCallOnNewMessageOnAllExtensions()
    {
        // Arrange
        var manager = new ConversationStateExtensionsManager();
        var mockExtension = new Mock<ConversationStateExtension>();
        var message = new ChatMessage(ChatRole.User, "Hello");
        manager.Add(mockExtension.Object);

        // Act
        await manager.OnNewMessageAsync("test-thread-id", message);

        // Assert
        mockExtension.Verify(x => x.OnNewMessageAsync("test-thread-id", message, It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnAIInvocationAsyncShouldAggregateContextsFromAllExtensions()
    {
        // Arrange
        var manager = new ConversationStateExtensionsManager();
        var mockExtension1 = new Mock<ConversationStateExtension>();
        var mockExtension2 = new Mock<ConversationStateExtension>();
        mockExtension1.Setup(x => x.OnModelInvokeAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                      .ReturnsAsync("Context1");
        mockExtension2.Setup(x => x.OnModelInvokeAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                      .ReturnsAsync("Context2");
        manager.Add(mockExtension1.Object);
        manager.Add(mockExtension2.Object);

        var messages = new List<ChatMessage>();

        // Act
        var result = await manager.OnModelInvokeAsync(messages);

        // Assert
        Assert.Equal("Context1\nContext2", result);
    }

    [Fact]
    public async Task OnSuspendAsyncShouldCallOnSuspendOnAllExtensions()
    {
        // Arrange
        var manager = new ConversationStateExtensionsManager();
        var mockExtension = new Mock<ConversationStateExtension>();
        manager.Add(mockExtension.Object);

        // Act
        await manager.OnSuspendAsync("test-thread-id");

        // Assert
        mockExtension.Verify(x => x.OnSuspendAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task OnResumeAsyncShouldCallOnResumeOnAllExtensions()
    {
        // Arrange
        var manager = new ConversationStateExtensionsManager();
        var mockExtension = new Mock<ConversationStateExtension>();
        manager.Add(mockExtension.Object);

        // Act
        await manager.OnResumeAsync("test-thread-id");

        // Assert
        mockExtension.Verify(x => x.OnResumeAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }
}
