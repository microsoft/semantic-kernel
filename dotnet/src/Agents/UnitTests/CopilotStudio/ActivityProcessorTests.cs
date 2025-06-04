// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Agents.Core.Models;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.CopilotStudio.Internal;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.CopilotStudio;

/// <summary>
/// Unit tests for the ActivityProcessor class.
/// </summary>
public class ActivityProcessorTests
{
    /// <summary>
    /// Tests that a message activity is processed and returns a ChatMessageContent with assistant role and correct content.
    /// </summary>
    [Fact]
    public async Task ProcessActivity_WithMessageActivity_ReturnsAssistantChatMessageContent()
    {
        // Arrange
        Activity messageActivity = new()
        {
            Type = "message",
            Text = "Hello, I'm Copilot!"
        };

        IAsyncEnumerable<IActivity> activities = CreateAsyncEnumerable(new[] { messageActivity });
        Mock<ILogger> loggerMock = new();

        // Act
        ChatMessageContent[] results = await ActivityProcessor.ProcessActivity(activities, loggerMock.Object)
            .ToArrayAsync();

        // Assert
        Assert.Single(results);
        ChatMessageContent chatMessage = results[0];
        Assert.Equal(AuthorRole.Assistant, chatMessage.Role);
        Assert.Equal("Hello, I'm Copilot!", chatMessage.Content);
        Assert.Same(messageActivity, chatMessage.InnerContent);
    }

    /// <summary>
    /// Tests that a typing activity is processed and returns a ChatMessageContent with assistant role and ReasoningContent item.
    /// </summary>
    [Fact]
    public async Task ProcessActivity_WithTypingActivity_ReturnsAssistantReasoningContent()
    {
        // Arrange
        Activity typingActivity = new()
        {
            Type = "typing"
        };

        IAsyncEnumerable<IActivity> activities = CreateAsyncEnumerable(new[] { typingActivity });
        Mock<ILogger> loggerMock = new(MockBehavior.Strict);

        // Act
        ChatMessageContent[] results = await ActivityProcessor.ProcessActivity(activities, loggerMock.Object).ToArrayAsync();

        // Assert
        Assert.Single(results);
        ChatMessageContent chatMessage = results[0];
        Assert.Equal(AuthorRole.Assistant, chatMessage.Role);
        Assert.Single(chatMessage.Items);
        Assert.IsType<ReasoningContent>(chatMessage.Items[0]);
        Assert.Same(typingActivity, chatMessage.InnerContent);
    }

    /// <summary>
    /// Tests that an event activity is processed and returns no ChatMessageContent.
    /// </summary>
    [Fact]
    public async Task ProcessActivity_WithEventActivity_ReturnsNoMessages()
    {
        // Arrange
        Activity eventActivity = new()
        {
            Type = "event"
        };

        IAsyncEnumerable<IActivity> activities = CreateAsyncEnumerable(new[] { eventActivity });
        Mock<ILogger> loggerMock = new(MockBehavior.Strict);

        // Act
        ChatMessageContent[] results = await ActivityProcessor.ProcessActivity(activities, loggerMock.Object).ToArrayAsync();

        // Assert
        Assert.Empty(results);
    }

    /// <summary>
    /// Tests that an unknown activity type is processed and logs a warning.
    /// </summary>
    [Fact]
    public async Task ProcessActivity_WithUnknownActivity_LogsWarning()
    {
        // Arrange
        Activity unknownActivity = new()
        {
            Type = "unknown_type"
        };

        IAsyncEnumerable<IActivity> activities = CreateAsyncEnumerable(new[] { unknownActivity });
        Mock<ILogger> loggerMock = new();

        // Act
        ChatMessageContent[] results = await ActivityProcessor.ProcessActivity(activities, loggerMock.Object).ToArrayAsync();

        // Assert
        Assert.Empty(results);
        loggerMock.Verify(
            x => x.Log(
                LogLevel.Warning,
                It.IsAny<EventId>(),
                It.Is<It.IsAnyType>((v, t) => true),
                It.IsAny<Exception>(),
                It.Is<Func<It.IsAnyType, Exception?, string>>((v, t) => true)),
            Times.Once);
    }

    /// <summary>
    /// Tests that a message activity with suggested actions returns a ChatMessageContent with action items.
    /// </summary>
    [Fact]
    public async Task ProcessActivity_WithSuggestedActions_ReturnsMessageWithActions()
    {
        // Arrange
        Activity messageActivity = new()
        {
            Type = "message",
            Text = "Select an option:",
            SuggestedActions = new SuggestedActions
            {
                Actions = new[]
                {
                    new CardAction { Title = "Option 1" },
                    new CardAction { Title = "Option 2" }
                }
            }
        };

        IAsyncEnumerable<IActivity> activities = CreateAsyncEnumerable(new[] { messageActivity });
        Mock<ILogger> loggerMock = new(MockBehavior.Strict);

        // Act
        ChatMessageContent[] results = await ActivityProcessor.ProcessActivity(activities, loggerMock.Object).ToArrayAsync();

        // Assert
        Assert.Single(results);
        ChatMessageContent chatMessage = results[0];
        Assert.Equal(AuthorRole.Assistant, chatMessage.Role);
        Assert.Equal("Select an option:", chatMessage.Content);
        Assert.Equal(3, chatMessage.Items.Count); // Text content + 2 action contents
        Assert.IsType<TextContent>(chatMessage.Items[0]);
        Assert.IsType<ActionContent>(chatMessage.Items[1]);
        Assert.IsType<ActionContent>(chatMessage.Items[2]);
        Assert.Equal("Option 1", ((ActionContent)chatMessage.Items[1]).Text);
        Assert.Equal("Option 2", ((ActionContent)chatMessage.Items[2]).Text);
    }

    /// <summary>
    /// Tests that multiple activities are processed and all valid activities are returned as ChatMessageContent.
    /// </summary>
    [Fact]
    public async Task ProcessActivity_WithMultipleActivities_ProcessesAllActivities()
    {
        // Arrange
        Activity messageActivity = new()
        {
            Type = "message",
            Text = "Hello"
        };

        Activity typingActivity = new()
        {
            Type = "typing"
        };

        Activity eventActivity = new()
        {
            Type = "event"
        };

        IAsyncEnumerable<IActivity> activities = CreateAsyncEnumerable(
            [messageActivity, typingActivity, eventActivity]);
        Mock<ILogger> loggerMock = new(MockBehavior.Strict);

        // Act
        ChatMessageContent[] results = await ActivityProcessor.ProcessActivity(activities, loggerMock.Object).ToArrayAsync();

        // Assert
        Assert.Equal(2, results.Length);
        Assert.Equal("Hello", results[0].Content);
        Assert.IsType<ReasoningContent>(results[1].Items[0]);
    }

    /// <summary>
    /// Helper method to create an IAsyncEnumerable from a collection of IActivity.
    /// </summary>
    /// <param name="activities">The activities to yield.</param>
    /// <returns>An async enumerable of IActivity.</returns>
    private static IAsyncEnumerable<IActivity> CreateAsyncEnumerable(IEnumerable<IActivity> activities) => activities.ToAsyncEnumerable();
}
