// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
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
