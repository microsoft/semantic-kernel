// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.History;

/// <summary>
/// %%%
/// </summary>
public class ChatHistoryReducerExtensionsTests
{
    /// <summary>
    /// %%%
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
        ChatHistory history = [.. MockHistoryGenerator.CreateSimpleHistory(messageCount)];

        ChatMessageContent[] extractedHistory = history.Extract(startIndex, endIndex).ToArray();

        int finalIndex = endIndex ?? messageCount - 1;
        finalIndex = Math.Min(finalIndex, messageCount - 1);

        expectedCount ??= finalIndex - startIndex + 1;

        Assert.Equal(expectedCount, extractedHistory.Length);

        if (extractedHistory.Length > 0)
        {
            Assert.Contains($"#{startIndex}", extractedHistory[0].Content);
            Assert.Contains($"#{finalIndex}", extractedHistory[^1].Content);
        }
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Theory]
    [InlineData(0, 100)]
    [InlineData(1, 100)]
    [InlineData(100, 10)]
    [InlineData(100, 0)]
    public void VerifyGetFinalSummaryIndex(int summaryCount, int regularCount)
    {
        ChatHistory summaries = [.. MockHistoryGenerator.CreateSimpleHistory(summaryCount)];
        foreach (ChatMessageContent summary in summaries)
        {
            summary.Metadata = new Dictionary<string, object?>() { { "summary", true } };
        }

        ChatHistory history = [.. summaries, .. MockHistoryGenerator.CreateSimpleHistory(regularCount)];

        int finalSummaryIndex = history.LocateSummarizationBoundary("summary");

        Assert.Equal(summaryCount, finalSummaryIndex);
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryNotReducedAsync()
    {
        ChatHistory history = [];

        (bool isReduced, ChatHistory reducedHistory) = await history.ReduceAsync(null, default);

        Assert.False(isReduced);
        Assert.StrictEqual(history, reducedHistory);

        Mock<IChatHistoryReducer> mockReducer = new();
        mockReducer.Setup(r => r.ReduceAsync(It.IsAny<IReadOnlyList<ChatMessageContent>>(), default)).ReturnsAsync((IEnumerable<ChatMessageContent>?)null);
        (isReduced, reducedHistory) = await history.ReduceAsync(mockReducer.Object, default);

        Assert.False(isReduced);
        Assert.StrictEqual(history, reducedHistory);
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryReducedAsync()
    {
        Mock<IChatHistoryReducer> mockReducer = new();
        mockReducer.Setup(r => r.ReduceAsync(It.IsAny<IReadOnlyList<ChatMessageContent>>(), default)).ReturnsAsync((IEnumerable<ChatMessageContent>?)[]);

        ChatHistory history = [];

        (bool isReduced, ChatHistory reducedHistory) = await history.ReduceAsync(mockReducer.Object, default);

        Assert.True(isReduced);
        Assert.NotStrictEqual(history, reducedHistory);
    }
}
