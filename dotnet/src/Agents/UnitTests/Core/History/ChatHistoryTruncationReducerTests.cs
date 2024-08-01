// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.History;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.History;

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
    public void VerifyChatHistoryConstructorArgumentValidation(int targetCount, int? thresholdCount = null)
    {
        Assert.Throws<ArgumentException>(() => new ChatHistoryTruncationReducer(targetCount, thresholdCount));
    }

    /// <summary>
    /// Validate hash-code expresses reducer equivalency.
    /// </summary>
    [Fact]
    public void VerifyChatHistoryHasCode()
    {
        HashSet<ChatHistoryTruncationReducer> reducers = [];

        int hashCode1 = GenerateHashCode(3, 4);
        int hashCode2 = GenerateHashCode(33, 44);
        int hashCode3 = GenerateHashCode(3000, 4000);
        int hashCode4 = GenerateHashCode(3000, 4000);

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
        IReadOnlyList<ChatMessageContent> sourceHistory = MockHistoryGenerator.CreateSimpleHistory(10).ToArray();

        ChatHistoryTruncationReducer reducer = new(20);
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        Assert.Null(reducedHistory);
    }

    /// <summary>
    /// Validate history reduced when source history exceeds target threshold.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryReducedAsync()
    {
        IReadOnlyList<ChatMessageContent> sourceHistory = MockHistoryGenerator.CreateSimpleHistory(20).ToArray();

        ChatHistoryTruncationReducer reducer = new(10);
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        VerifyReducedHistory(reducedHistory, 10);
    }

    /// <summary>
    /// Validate history re-summarized on second occurrence of source history exceeding target threshold.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryRereducedAsync()
    {
        IReadOnlyList<ChatMessageContent> sourceHistory = MockHistoryGenerator.CreateSimpleHistory(20).ToArray();

        ChatHistoryTruncationReducer reducer = new(10);
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);
        reducedHistory = await reducer.ReduceAsync([.. reducedHistory!, .. sourceHistory]);

        VerifyReducedHistory(reducedHistory, 10);
    }

    private static void VerifyReducedHistory(IEnumerable<ChatMessageContent>? reducedHistory, int expectedCount)
    {
        Assert.NotNull(reducedHistory);
        ChatMessageContent[] messages = reducedHistory.ToArray();
        Assert.Equal(expectedCount, messages.Length);
    }
}
