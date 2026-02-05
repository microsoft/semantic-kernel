// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core;

/// <summary>
/// Unit testing of <see cref="ChatReducerTriggerEvent"/> and related trigger-aware reducer functionality.
/// </summary>
public class ChatReducerTriggerEventTests
{
    /// <summary>
    /// Verify that ChatReducerTriggerEvent enum has the expected values.
    /// </summary>
    [Fact]
    public void VerifyChatReducerTriggerEventValues()
    {
        // Assert - verify all expected trigger events exist
        Assert.True(System.Enum.IsDefined(typeof(ChatReducerTriggerEvent), ChatReducerTriggerEvent.AfterMessageAdded));
        Assert.True(System.Enum.IsDefined(typeof(ChatReducerTriggerEvent), ChatReducerTriggerEvent.BeforeMessagesRetrieval));
        Assert.True(System.Enum.IsDefined(typeof(ChatReducerTriggerEvent), ChatReducerTriggerEvent.AfterToolCallResponseReceived));
    }

    /// <summary>
    /// Verify that a trigger-aware reducer responds to configured trigger events.
    /// </summary>
    [Fact]
    public async Task VerifyTriggerAwareReducerRespondsToConfiguredEventsAsync()
    {
        // Arrange
        var reducer = new TestTriggerAwareReducer(ChatReducerTriggerEvent.AfterToolCallResponseReceived);
        var history = new List<ChatMessageContent>
        {
            new(AuthorRole.User, "Test message 1"),
            new(AuthorRole.Assistant, "Test response 1"),
            new(AuthorRole.User, "Test message 2")
        };

        // Act - should trigger
        var shouldTrigger = reducer.ShouldTriggerOn(ChatReducerTriggerEvent.AfterToolCallResponseReceived);
        
        // Assert
        Assert.True(shouldTrigger);
        Assert.Single(reducer.TriggerEvents);
        Assert.Contains(ChatReducerTriggerEvent.AfterToolCallResponseReceived, reducer.TriggerEvents);
    }

    /// <summary>
    /// Verify that a trigger-aware reducer does not respond to non-configured trigger events.
    /// </summary>
    [Fact]
    public void VerifyTriggerAwareReducerIgnoresNonConfiguredEvents()
    {
        // Arrange
        var reducer = new TestTriggerAwareReducer(ChatReducerTriggerEvent.AfterToolCallResponseReceived);

        // Act & Assert - should not trigger for other events
        Assert.False(reducer.ShouldTriggerOn(ChatReducerTriggerEvent.AfterMessageAdded));
        Assert.False(reducer.ShouldTriggerOn(ChatReducerTriggerEvent.BeforeMessagesRetrieval));
    }

    /// <summary>
    /// Verify that a trigger-aware reducer can be configured for multiple events.
    /// </summary>
    [Fact]
    public void VerifyTriggerAwareReducerSupportsMultipleEvents()
    {
        // Arrange
        var reducer = new TestTriggerAwareReducer(
            ChatReducerTriggerEvent.AfterToolCallResponseReceived,
            ChatReducerTriggerEvent.BeforeMessagesRetrieval);

        // Act & Assert
        Assert.True(reducer.ShouldTriggerOn(ChatReducerTriggerEvent.AfterToolCallResponseReceived));
        Assert.True(reducer.ShouldTriggerOn(ChatReducerTriggerEvent.BeforeMessagesRetrieval));
        Assert.False(reducer.ShouldTriggerOn(ChatReducerTriggerEvent.AfterMessageAdded));
        Assert.Equal(2, reducer.TriggerEvents.Count);
    }

    /// <summary>
    /// Verify that a reducer without triggers defaults to BeforeMessagesRetrieval.
    /// </summary>
    [Fact]
    public void VerifyReducerDefaultsTriggerToBeforeMessagesRetrieval()
    {
        // Arrange & Act
        var reducer = new TestTriggerAwareReducer();

        // Assert
        Assert.Single(reducer.TriggerEvents);
        Assert.Contains(ChatReducerTriggerEvent.BeforeMessagesRetrieval, reducer.TriggerEvents);
        Assert.True(reducer.ShouldTriggerOn(ChatReducerTriggerEvent.BeforeMessagesRetrieval));
    }

    /// <summary>
    /// Test implementation of a trigger-aware reducer for testing purposes.
    /// </summary>
    private sealed class TestTriggerAwareReducer : ChatHistoryReducerBase
    {
        public TestTriggerAwareReducer(params ChatReducerTriggerEvent[] triggerEvents)
            : base(triggerEvents)
        {
        }

        public override Task<IEnumerable<ChatMessageContent>?> ReduceAsync(
            IReadOnlyList<ChatMessageContent> chatHistory,
            CancellationToken cancellationToken = default)
        {
            // Simple test implementation: keep only the last 2 messages
            if (chatHistory.Count > 2)
            {
                return Task.FromResult<IEnumerable<ChatMessageContent>?>(
                    chatHistory.Skip(chatHistory.Count - 2).ToList());
            }

            return Task.FromResult<IEnumerable<ChatMessageContent>?>(null);
        }
    }
}
