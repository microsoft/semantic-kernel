// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core;

/// <summary>
/// Contains tests for the <see cref="ChatHistoryAgentThread"/> class.
/// </summary>
public class ChatHistoryAgentThreadTests
{
    /// <summary>
    /// Tests that creating a thread generates a unique Id and doesn't change IsDeleted.
    /// </summary>
    [Fact]
    public async Task CreateShouldGenerateIdAsync()
    {
        // Arrange
        var thread = new ChatHistoryAgentThread();

        // Act
        await thread.CreateAsync();

        // Assert
        Assert.NotNull(thread.Id);
        Assert.False(thread.IsDeleted);
    }

    /// <summary>
    /// Tests that deleting a thread marks it as deleted.
    /// </summary>
    [Fact]
    public async Task DeleteShouldMarkThreadAsDeletedAsync()
    {
        // Arrange
        var thread = new ChatHistoryAgentThread();
        await thread.CreateAsync();

        // Act
        await thread.DeleteAsync();

        // Assert
        Assert.True(thread.IsDeleted);
    }

    /// <summary>
    /// Tests that adding a new message to the thread adds it to the message history.
    /// </summary>
    [Fact]
    public async Task OnNewMessageShouldAddMessageToHistoryAsync()
    {
        // Arrange
        var thread = new ChatHistoryAgentThread();
        var message = new ChatMessageContent(AuthorRole.User, "Hello");

        // Act
        await thread.OnNewMessageAsync(message);

        // Assert
        var messages = await thread.GetMessagesAsync().ToListAsync();
        Assert.Single(messages);
        Assert.Equal("Hello", messages[0].Content);
    }

    /// <summary>
    /// Tests that GetMessagesAsync returns all messages in the thread.
    /// </summary>
    [Fact]
    public async Task GetMessagesShouldReturnAllMessagesAsync()
    {
        // Arrange
        var thread = new ChatHistoryAgentThread();
        var message1 = new ChatMessageContent(AuthorRole.User, "Hello");
        var message2 = new ChatMessageContent(AuthorRole.Assistant, "Hi there");

        await thread.OnNewMessageAsync(message1);
        await thread.OnNewMessageAsync(message2);

        // Act
        var messages = await thread.GetMessagesAsync().ToListAsync();

        // Assert
        Assert.Equal(2, messages.Count);
        Assert.Equal("Hello", messages[0].Content);
        Assert.Equal("Hi there", messages[1].Content);
    }

    /// <summary>
    /// Tests that GetMessagesAsync throws an InvalidOperationException if the thread is deleted.
    /// </summary>
    [Fact]
    public async Task GetMessagesShouldThrowIfThreadIsDeletedAsync()
    {
        // Arrange
        var thread = new ChatHistoryAgentThread();
        await thread.CreateAsync();
        await thread.DeleteAsync();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await thread.GetMessagesAsync().ToListAsync());
    }

    /// <summary>
    /// Tests that GetMessagesAsync creates the thread if it has not been created yet.
    /// </summary>
    [Fact]
    public async Task GetMessagesShouldCreateThreadIfNotCreatedAsync()
    {
        // Arrange
        var thread = new ChatHistoryAgentThread();

        // Act
        var messages = await thread.GetMessagesAsync().ToListAsync();

        // Assert
        Assert.NotNull(thread.Id);
        Assert.False(thread.IsDeleted);
        Assert.Empty(messages);
    }
}
