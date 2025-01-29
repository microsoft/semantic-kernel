// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.AI.ChatCompletion;

/// <summary>
/// Unit testing of <see cref="ChatHistoryTruncationReducer"/>.
/// </summary>
public class ChatHistoryTruncationReducerTests
{
    /// <summary>
    /// Ensure that the constructor arguments are validated.
    /// </summary>
    [Theory]
    [InlineData(-1)]
    [InlineData(-1, int.MaxValue)]
    [InlineData(int.MaxValue, -1)]
    public void VerifyConstructorArgumentValidation(int targetCount, int? thresholdCount = null)
    {
        // Act and Assert
        Assert.Throws<ArgumentException>(() => new ChatHistoryTruncationReducer(targetCount, thresholdCount));
    }

    /// <summary>
    /// Validate equality override.
    /// </summary>
    [Fact]
    public void VerifyEquality()
    {
        // Arrange
        ChatHistoryTruncationReducer reducer1 = new(3, 3);
        ChatHistoryTruncationReducer reducer2 = new(3, 3);
        ChatHistoryTruncationReducer reducer3 = new(4, 3);
        ChatHistoryTruncationReducer reducer4 = new(3, 5);
        ChatHistoryTruncationReducer reducer5 = new(3);
        ChatHistoryTruncationReducer reducer6 = new(3);

        // Assert
        Assert.True(reducer1.Equals(reducer1));
        Assert.True(reducer1.Equals(reducer2));
        Assert.True(reducer5.Equals(reducer6));
        Assert.True(reducer3.Equals(reducer3));
        Assert.False(reducer1.Equals(reducer3));
        Assert.False(reducer1.Equals(reducer4));
        Assert.False(reducer1.Equals(reducer5));
        Assert.False(reducer1.Equals(reducer6));
        Assert.False(reducer1.Equals(null));
    }

    /// <summary>
    /// Validate hash-code expresses reducer equivalency.
    /// </summary>
    [Fact]
    public void VerifyHashCode()
    {
        // Arrange
        HashSet<ChatHistoryTruncationReducer> reducers = [];

        // Act
        int hashCode1 = GenerateHashCode(3, 4);
        int hashCode2 = GenerateHashCode(33, 44);
        int hashCode3 = GenerateHashCode(3000, 4000);
        int hashCode4 = GenerateHashCode(3000, 4000);

        // Assert
        Assert.NotEqual(hashCode1, hashCode2);
        Assert.NotEqual(hashCode2, hashCode3);
        Assert.Equal(hashCode3, hashCode4);
        Assert.Equal(3, reducers.Count);

        int GenerateHashCode(int targetCount, int thresholdCount)
        {
            ChatHistoryTruncationReducer reducer = new(targetCount, thresholdCount);

            reducers.Add(reducer);

            return reducer.GetHashCode();
        }
    }

    /// <summary>
    /// Validate history not reduced when source history does not exceed target threshold.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryNotReducedAsync()
    {
        // Arrange
        IReadOnlyList<ChatMessageContent> sourceHistory = MockChatHistoryGenerator.CreateSimpleHistory(10).ToArray();
        ChatHistoryTruncationReducer reducer = new(20);

        // Act
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        // Assert
        Assert.Null(reducedHistory);
    }

    /// <summary>
    /// Validate history reduced when source history exceeds target threshold.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryReducedAsync()
    {
        // Arrange
        IReadOnlyList<ChatMessageContent> sourceHistory = MockChatHistoryGenerator.CreateSimpleHistory(20).ToArray();
        ChatHistoryTruncationReducer reducer = new(10);

        // Act
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        // Assert
        VerifyReducedHistory(reducedHistory, 10);
    }

    /// <summary>
    /// Validate history re-summarized on second occurrence of source history exceeding target threshold.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryRereducedAsync()
    {
        // Arrange
        IReadOnlyList<ChatMessageContent> sourceHistory = MockChatHistoryGenerator.CreateSimpleHistory(20).ToArray();
        ChatHistoryTruncationReducer reducer = new(10);

        // Act
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);
        reducedHistory = await reducer.ReduceAsync([.. reducedHistory!, .. sourceHistory]);

        // Assert
        VerifyReducedHistory(reducedHistory, 10);
    }

    /// <summary>
    /// Validate history reduced and system message preserved when source history exceeds target threshold.
    /// </summary>
    [Fact]
    public async Task VerifySystemMessageIsNotReducedAsync()
    {
        // Arrange
        IReadOnlyList<ChatMessageContent> sourceHistory = MockChatHistoryGenerator.CreateSimpleHistory(20, includeSystemMessage: true).ToArray();
        ChatHistoryTruncationReducer reducer = new(10);

        // Act
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        // Assert
        VerifyReducedHistory(reducedHistory, 10);
        Assert.Contains(reducedHistory!, m => m.Role == AuthorRole.System);
    }

    private static void VerifyReducedHistory(IEnumerable<ChatMessageContent>? reducedHistory, int expectedCount)
    {
        Assert.NotNull(reducedHistory);
        ChatMessageContent[] messages = reducedHistory.ToArray();
        Assert.Equal(expectedCount, messages.Length);
    }
}
