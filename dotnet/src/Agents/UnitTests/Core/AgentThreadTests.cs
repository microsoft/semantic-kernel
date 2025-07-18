// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core;

/// <summary>
/// Contains tests for the <see cref="AgentThread"/> class.
/// </summary>
public class AgentThreadTests
{
    /// <summary>
    /// Tests that the CreateAsync method sets the Id and invokes CreateInternalAsync once.
    /// </summary>
    [Fact]
    public async Task CreateShouldSetIdAndInvokeCreateInternalOnceAsync()
    {
        // Arrange
        var thread = new TestAgentThread();

        // Act
        await thread.CreateAsync();
        await thread.CreateAsync();

        // Assert
        Assert.Equal("test-thread-id", thread.Id);
        Assert.Equal(1, thread.CreateInternalAsyncCount);
    }

    /// <summary>
    /// Tests that the CreateAsync method throws an InvalidOperationException if the thread is deleted.
    /// </summary>
    [Fact]
    public async Task CreateShouldThrowIfThreadDeletedAsync()
    {
        // Arrange
        var thread = new TestAgentThread();
        await thread.CreateAsync();
        await thread.DeleteAsync();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => thread.CreateAsync());
        Assert.Equal(1, thread.CreateInternalAsyncCount);
        Assert.Equal(1, thread.DeleteInternalAsyncCount);
    }

    /// <summary>
    /// Tests that the DeleteAsync method sets IsDeleted and invokes DeleteInternalAsync.
    /// </summary>
    [Fact]
    public async Task DeleteShouldSetIsDeletedAndInvokeDeleteInternalAsync()
    {
        // Arrange
        var thread = new TestAgentThread();
        await thread.CreateAsync();

        // Act
        await thread.DeleteAsync();

        // Assert
        Assert.True(thread.IsDeleted);
        Assert.Equal(1, thread.CreateInternalAsyncCount);
        Assert.Equal(1, thread.DeleteInternalAsyncCount);
    }

    /// <summary>
    /// Tests that the DeleteAsync method does not invoke DeleteInternalAsync if the thread is already deleted.
    /// </summary>
    [Fact]
    public async Task DeleteShouldNotInvokeDeleteInternalIfAlreadyDeletedAsync()
    {
        // Arrange
        var thread = new TestAgentThread();
        await thread.CreateAsync();
        await thread.DeleteAsync();

        // Act
        await thread.DeleteAsync();

        // Assert
        Assert.True(thread.IsDeleted);
        Assert.Equal(1, thread.CreateInternalAsyncCount);
        Assert.Equal(1, thread.DeleteInternalAsyncCount);
    }

    /// <summary>
    /// Tests that the DeleteAsync method throws an InvalidOperationException if the thread was never created.
    /// </summary>
    [Fact]
    public async Task DeleteShouldThrowIfNeverCreatedAsync()
    {
        // Arrange
        var thread = new TestAgentThread();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => thread.DeleteAsync());
        Assert.Equal(0, thread.CreateInternalAsyncCount);
        Assert.Equal(0, thread.DeleteInternalAsyncCount);
    }

    /// <summary>
    /// Tests that the OnNewMessageAsync method creates the thread if it is not already created.
    /// </summary>
    [Fact]
    public async Task OnNewMessageShouldCreateThreadIfNotCreatedAsync()
    {
        // Arrange
        var thread = new TestAgentThread();
        var message = new ChatMessageContent();

        // Act
        await thread.OnNewMessageAsync(message);

        // Assert
        Assert.Equal("test-thread-id", thread.Id);
        Assert.Equal(1, thread.CreateInternalAsyncCount);
        Assert.Equal(1, thread.OnNewMessageInternalAsyncCount);
    }

    /// <summary>
    /// Tests that the OnNewMessageAsync method throws an InvalidOperationException if the thread is deleted.
    /// </summary>
    [Fact]
    public async Task OnNewMessageShouldThrowIfThreadDeletedAsync()
    {
        // Arrange
        var thread = new TestAgentThread();
        await thread.CreateAsync();
        await thread.DeleteAsync();
        var message = new ChatMessageContent();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => thread.OnNewMessageAsync(message));
        Assert.Equal(1, thread.CreateInternalAsyncCount);
        Assert.Equal(1, thread.DeleteInternalAsyncCount);
        Assert.Equal(0, thread.OnNewMessageInternalAsyncCount);
    }

    /// <summary>
    /// Tests that the <see cref="AgentThread.OnResumeAsync(CancellationToken)"/> method throws an InvalidOperationException if the thread is not yet created.
    /// </summary>
    [Fact]
    public async Task OnResumeShouldThrowIfThreadNotCreatedAsync()
    {
        // Arrange
        var thread = new TestAgentThread();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => thread.OnResumeAsync());
    }

    /// <summary>
    /// Tests that the <see cref="AgentThread.OnResumeAsync(CancellationToken)"/> method throws an InvalidOperationException if the thread is deleted.
    /// </summary>
    [Fact]
    public async Task OnResumeShouldThrowIfThreadDeletedAsync()
    {
        // Arrange
        var thread = new TestAgentThread();
        await thread.CreateAsync();
        await thread.DeleteAsync();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() => thread.OnResumeAsync());
    }

    /// <summary>
    /// Tests that the <see cref="AgentThread.OnSuspendAsync(CancellationToken)"/> method
    /// calls each registered state part in turn.
    /// </summary>
    [Fact]
    public async Task OnSuspendShouldCallOnSuspendOnRegisteredPartsAsync()
    {
        // Arrange.
        var thread = new TestAgentThread();
        var mockProvider = new Mock<AIContextProvider>();
        thread.AIContextProviders.Add(mockProvider.Object);
        await thread.CreateAsync();

        // Act.
        await thread.OnSuspendAsync();

        // Assert.
        mockProvider.Verify(x => x.SuspendingAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    /// <summary>
    /// Tests that the <see cref="AgentThread.OnResumeAsync(CancellationToken)"/> method
    /// calls each registered state part in turn.
    /// </summary>
    [Fact]
    public async Task OnResumeShouldCallOnResumeOnRegisteredPartsAsync()
    {
        // Arrange.
        var thread = new TestAgentThread();
        var mockProvider = new Mock<AIContextProvider>();
        thread.AIContextProviders.Add(mockProvider.Object);
        await thread.CreateAsync();

        // Act.
        await thread.OnResumeAsync();

        // Assert.
        mockProvider.Verify(x => x.ResumingAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    /// <summary>
    /// Tests that the <see cref="AgentThread.CreateAsync(CancellationToken)"/> method
    /// calls each registered state parts in turn.
    /// </summary>
    [Fact]
    public async Task CreateShouldCallOnThreadCreatedOnRegisteredPartsAsync()
    {
        // Arrange.
        var thread = new TestAgentThread();
        var mockProvider = new Mock<AIContextProvider>();
        thread.AIContextProviders.Add(mockProvider.Object);

        // Act.
        await thread.CreateAsync();

        // Assert.
        mockProvider.Verify(x => x.ConversationCreatedAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    /// <summary>
    /// Tests that the <see cref="AgentThread.DeleteAsync(CancellationToken)"/> method
    /// calls each registered state parts in turn.
    /// </summary>
    [Fact]
    public async Task DeleteShouldCallOnThreadDeleteOnRegisteredPartsAsync()
    {
        // Arrange.
        var thread = new TestAgentThread();
        var mockProvider = new Mock<AIContextProvider>();
        thread.AIContextProviders.Add(mockProvider.Object);
        await thread.CreateAsync();

        // Act.
        await thread.DeleteAsync();

        // Assert.
        mockProvider.Verify(x => x.ConversationDeletingAsync("test-thread-id", It.IsAny<CancellationToken>()), Times.Once);
    }

    /// <summary>
    /// Tests that the <see cref="AgentThread.OnNewMessageAsync(ChatMessageContent, CancellationToken)"/> method
    /// calls each registered state part in turn.
    /// </summary>
    [Fact]
    public async Task OnNewMessageShouldCallOnNewMessageOnRegisteredPartsAsync()
    {
        // Arrange.
        var thread = new TestAgentThread();
        var mockProvider = new Mock<AIContextProvider>();
        thread.AIContextProviders.Add(mockProvider.Object);
        var message = new ChatMessageContent(AuthorRole.User, "Test Message.");

        await thread.CreateAsync();

        // Act.
        await thread.OnNewMessageAsync(message);

        // Assert.
        mockProvider.Verify(x => x.MessageAddingAsync("test-thread-id", It.Is<ChatMessage>(x => x.Text == "Test Message." && x.Role == ChatRole.User), It.IsAny<CancellationToken>()), Times.Once);
    }

    private sealed class TestAgentThread : AgentThread
    {
        public int CreateInternalAsyncCount { get; private set; }
        public int DeleteInternalAsyncCount { get; private set; }
        public int OnNewMessageInternalAsyncCount { get; private set; }

        public new Task CreateAsync(CancellationToken cancellationToken = default)
        {
            return base.CreateAsync(cancellationToken);
        }

        protected override Task<string?> CreateInternalAsync(CancellationToken cancellationToken)
        {
            this.CreateInternalAsyncCount++;
            return Task.FromResult<string?>("test-thread-id");
        }

        protected override Task DeleteInternalAsync(CancellationToken cancellationToken)
        {
            this.DeleteInternalAsyncCount++;
            return Task.CompletedTask;
        }

        protected override Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
        {
            this.OnNewMessageInternalAsyncCount++;
            return Task.CompletedTask;
        }
    }
}
