// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.AI.ChatCompletion;

/// <summary>
/// Unit testing of <see cref="ChatHistoryReducerExtensions"/>.
/// </summary>
public class ChatHistoryReducerExtensionsTests
{
    /// <summary>
    /// Verify the extraction of a set of messages from an input set.
    /// </summary>
    [Theory]
    [InlineData(100, 0, 1)]
    [InlineData(100, 0, 9)]
    [InlineData(100, 0, 99)]
    [InlineData(100, 80)]
    [InlineData(100, 80, 81)]
    [InlineData(100, 0)]
    [InlineData(100, int.MaxValue, null, 0)]
    [InlineData(100, 0, int.MaxValue, 100)]
    public void VerifyChatHistoryExtraction(int messageCount, int startIndex, int? endIndex = null, int? expectedCount = null)
    {
        // Arrange
        ChatHistory history = [.. MockChatHistoryGenerator.CreateSimpleHistory(messageCount)];

        // Act
        ChatMessageContent[] extractedHistory = history.Extract(startIndex, endIndex).ToArray();

        int finalIndex = endIndex ?? messageCount - 1;
        finalIndex = Math.Min(finalIndex, messageCount - 1);

        expectedCount ??= finalIndex - startIndex + 1;

        // Assert
        Assert.Equal(expectedCount, extractedHistory.Length);

        if (extractedHistory.Length > 0)
        {
            Assert.Contains($"#{startIndex}", extractedHistory[0].Content);
            Assert.Contains($"#{finalIndex}", extractedHistory[^1].Content);
        }
    }

    /// <summary>
    /// Verify identifying the first non-summary message index.
    /// </summary>
    [Theory]
    [InlineData(0, 100)]
    [InlineData(1, 100)]
    [InlineData(100, 10)]
    [InlineData(100, 0)]
    public void VerifyGetFinalSummaryIndex(int summaryCount, int regularCount)
    {
        // Arrange
        ChatHistory summaries = [.. MockChatHistoryGenerator.CreateSimpleHistory(summaryCount)];
        foreach (ChatMessageContent summary in summaries)
        {
            summary.Metadata = new Dictionary<string, object?>() { { "summary", true } };
        }

        // Act
        ChatHistory history = [.. summaries, .. MockChatHistoryGenerator.CreateSimpleHistory(regularCount)];

        int finalSummaryIndex = history.LocateSummarizationBoundary("summary");

        // Assert
        Assert.Equal(summaryCount, finalSummaryIndex);
    }

    /// <summary>
    /// Verify a <see cref="ChatHistory"/> instance is not reduced.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryNotReducedAsync()
    {
        // Arrange
        ChatHistory history = [];
        Mock<IChatHistoryReducer> mockReducer = new();
        mockReducer.Setup(r => r.ReduceAsync(It.IsAny<IReadOnlyList<ChatMessageContent>>(), default)).ReturnsAsync((IEnumerable<ChatMessageContent>?)null);

        // Act
        bool isReduced = await history.ReduceInPlaceAsync(null, default);

        // Assert
        Assert.False(isReduced);
        Assert.Empty(history);

        // Act
        isReduced = await history.ReduceInPlaceAsync(mockReducer.Object, default);

        // Assert
        Assert.False(isReduced);
        Assert.Empty(history);
    }

    /// <summary>
    /// Verify a <see cref="ChatHistory"/> instance is reduced.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryReducedAsync()
    {
        // Arrange
        Mock<IChatHistoryReducer> mockReducer = new();
        mockReducer.Setup(r => r.ReduceAsync(It.IsAny<IReadOnlyList<ChatMessageContent>>(), default)).ReturnsAsync((IEnumerable<ChatMessageContent>?)[]);

        ChatHistory history = [.. MockChatHistoryGenerator.CreateSimpleHistory(10)];

        // Act
        bool isReduced = await history.ReduceInPlaceAsync(mockReducer.Object, default);

        // Assert
        Assert.True(isReduced);
        Assert.Empty(history);
    }

    /// <summary>
    /// Verify starting index (0) is identified when message count does not exceed the limit.
    /// </summary>
    [Theory]
    [InlineData(0, 1)]
    [InlineData(1, 1)]
    [InlineData(1, 2)]
    [InlineData(1, int.MaxValue)]
    [InlineData(5, 1, 5)]
    [InlineData(5, 4, 2)]
    [InlineData(5, 5, 1)]
    [InlineData(900, 500, 400)]
    [InlineData(900, 500, int.MaxValue)]
    public void VerifyLocateSafeReductionIndexNone(int messageCount, int targetCount, int? thresholdCount = null)
    {
        // Arrange: Shape of history doesn't matter since reduction is not expected
        ChatHistory sourceHistory = [.. MockChatHistoryGenerator.CreateHistoryWithUserInput(messageCount)];

        // Act
        int reductionIndex = sourceHistory.LocateSafeReductionIndex(targetCount, thresholdCount);

        // Assert
        Assert.Equal(-1, reductionIndex);
    }

    /// <summary>
    /// Verify the expected index ) is identified when message count exceeds the limit.
    /// </summary>
    [Theory]
    [InlineData(2, 1)]
    [InlineData(3, 2)]
    [InlineData(3, 1, 1)]
    [InlineData(6, 1, 4)]
    [InlineData(6, 4, 1)]
    [InlineData(6, 5)]
    [InlineData(1000, 500, 400)]
    [InlineData(1000, 500, 499)]
    public void VerifyLocateSafeReductionIndexFound(int messageCount, int targetCount, int? thresholdCount = null)
    {
        // Arrange: Generate history with only assistant messages
        ChatHistory sourceHistory = [.. MockChatHistoryGenerator.CreateSimpleHistory(messageCount)];

        // Act
        int reductionIndex = sourceHistory.LocateSafeReductionIndex(targetCount, thresholdCount);

        // Assert
        Assert.True(reductionIndex > 0);
        Assert.Equal(targetCount, messageCount - reductionIndex);
    }

    /// <summary>
    /// Verify the expected index ) is identified when message count exceeds the limit.
    /// History contains alternating user and assistant messages.
    /// </summary>
    [Theory]
    [InlineData(2, 1)]
    [InlineData(3, 2)]
    [InlineData(3, 1, 1)]
    [InlineData(6, 1, 4)]
    [InlineData(6, 4, 1)]
    [InlineData(6, 5)]
    [InlineData(1000, 500, 400)]
    [InlineData(1000, 500, 499)]
    public void VerifyLocateSafeReductionIndexFoundWithUser(int messageCount, int targetCount, int? thresholdCount = null)
    {
        // Arrange: Generate history with alternating user and assistant messages
        ChatHistory sourceHistory = [.. MockChatHistoryGenerator.CreateHistoryWithUserInput(messageCount)];

        // Act
        int reductionIndex = sourceHistory.LocateSafeReductionIndex(targetCount, thresholdCount);

        // Assert
        Assert.True(reductionIndex > 0);

        // Act: The reduction length should align with a user message, if threshold is specified
        bool hasThreshold = thresholdCount > 0;
        int expectedCount = targetCount + (hasThreshold && sourceHistory[^targetCount].Role != AuthorRole.User ? 1 : 0);

        // Assert
        Assert.Equal(expectedCount, messageCount - reductionIndex);
    }

    /// <summary>
    /// Verify the expected index ) is identified when message count exceeds the limit.
    /// History contains alternating user and assistant messages along with function
    /// related content.
    /// </summary>
    [Theory]
    [InlineData(4)]
    [InlineData(4, 3)]
    [InlineData(5)]
    [InlineData(5, 8)]
    [InlineData(6)]
    [InlineData(6, 7)]
    [InlineData(7)]
    [InlineData(8)]
    [InlineData(9)]
    public void VerifyLocateSafeReductionIndexWithFunctionContent(int targetCount, int? thresholdCount = null)
    {
        // Arrange: Generate a history with function call on index 5 and 9 and
        // function result on index 6 and 10 (total length: 14)
        ChatHistory sourceHistory = [.. MockChatHistoryGenerator.CreateHistoryWithFunctionContent()];

        ChatHistoryTruncationReducer reducer = new(targetCount, thresholdCount);

        // Act
        int reductionIndex = sourceHistory.LocateSafeReductionIndex(targetCount, thresholdCount);

        // Assert
        Assert.True(reductionIndex > 0);

        // The reduction length avoid splitting function call and result, regardless of threshold
        int expectedCount = targetCount;

        if (sourceHistory[sourceHistory.Count - targetCount].Items.Any(i => i is FunctionCallContent))
        {
            expectedCount++;
        }
        else if (sourceHistory[sourceHistory.Count - targetCount].Items.Any(i => i is FunctionResultContent))
        {
            expectedCount += 2;
        }

        Assert.Equal(expectedCount, sourceHistory.Count - reductionIndex);
    }
}
