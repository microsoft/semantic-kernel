// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.History;

/// <summary>
/// %%%
/// </summary>
public class ChatHistoryTruncationReducerTests
{
    /// <summary>
    /// %%%
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
    /// %%%
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
    public async Task VerifyChatHistoryNotReducedAsync(int messageCount, int targetCount, int? thresholdCount = null)
    {
        // Shape of history doesn't matter since reduction is not expected
        ChatHistory sourceHistory = [.. GenerateHistory(messageCount)];

        ChatHistoryTruncationReducer reducer = new(targetCount, thresholdCount);

        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        Assert.Null(reducedHistory);
    }

    /// <summary>
    /// %%%
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
    public async Task VerifyChatHistoryReducedAsync(int messageCount, int targetCount, int? thresholdCount = null)
    {
        // Generate history with only assistant messages
        ChatHistory sourceHistory = [.. GenerateHistory(messageCount, skipUser: true)];

        ChatHistoryTruncationReducer reducer = new(targetCount, thresholdCount);

        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        Assert.NotNull(reducedHistory);
        ChatMessageContent[] messages = reducedHistory.ToArray();
        Assert.Equal(targetCount, messages.Length);
    }

    /// <summary>
    /// %%%
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
    public async Task VerifyChatHistoryReducedWithUserAsync(int messageCount, int targetCount, int? thresholdCount = null)
    {
        // Generate history with alternating user and assistant messages
        ChatHistory sourceHistory = [.. GenerateHistory(messageCount)];

        ChatHistoryTruncationReducer reducer = new(targetCount, thresholdCount);

        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        Assert.NotNull(reducedHistory);
        ChatMessageContent[] messages = reducedHistory.ToArray();

        // The reduction length should align with a user message, if threshold is specified
        bool hasThreshold = thresholdCount > 0;
        int expectedCount = targetCount + (hasThreshold && sourceHistory[^targetCount].Role != AuthorRole.User ? 1 : 0);

        Assert.Equal(expectedCount, messages.Length);
    }

    /// <summary>
    /// %%%
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
    public async Task VerifyChatHistoryReducedWithFunctionContentAsync(int targetCount, int? thresholdCount = null)
    {
        // Generate a history with function call on index 5 and 9 and
        // function result on index 6 and 10 (total length: 14)
        ChatHistory sourceHistory = [.. GenerateHistoryWithFunctionContent()];

        ChatHistoryTruncationReducer reducer = new(targetCount, thresholdCount);

        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        Assert.NotNull(reducedHistory);
        ChatMessageContent[] messages = reducedHistory.ToArray();

        // The reduction length avoid splitting function call and result, regardless of threshold
        int expectedCount = targetCount;

        if (sourceHistory[sourceHistory.Count - targetCount].Items.Any(i => i is FunctionCallContent))
        {
            expectedCount += 1;
        }
        else if (sourceHistory[sourceHistory.Count - targetCount].Items.Any(i => i is FunctionResultContent))
        {
            expectedCount += 2;
        }

        Assert.Equal(expectedCount, messages.Length);
    }

    private static IEnumerable<ChatMessageContent> GenerateHistory(int messageCount, bool skipUser = false)
    {
        for (int index = 0; index < messageCount; ++index)
        {
            yield return
                index % 2 == 1 || skipUser ?
                    new ChatMessageContent(AuthorRole.Assistant, $"asistant response: {index}") :
                    new ChatMessageContent(AuthorRole.User, $"user input: {index}");
        }
    }

    private static IEnumerable<ChatMessageContent> GenerateHistoryWithFunctionContent()
    {
        yield return new ChatMessageContent(AuthorRole.User, "user input: 0");
        yield return new ChatMessageContent(AuthorRole.Assistant, "asistant response: 1");
        yield return new ChatMessageContent(AuthorRole.User, "user input: 2");
        yield return new ChatMessageContent(AuthorRole.Assistant, "asistant response: 3");
        yield return new ChatMessageContent(AuthorRole.User, "user input: 4");
        yield return new ChatMessageContent(AuthorRole.Assistant, [new FunctionCallContent("function call: 5")]);
        yield return new ChatMessageContent(AuthorRole.Tool, [new FunctionResultContent("function result: 6")]);
        yield return new ChatMessageContent(AuthorRole.Assistant, "asistant response: 7");
        yield return new ChatMessageContent(AuthorRole.User, "user input: 8");
        yield return new ChatMessageContent(AuthorRole.Assistant, [new FunctionCallContent("function call: 9")]);
        yield return new ChatMessageContent(AuthorRole.Tool, [new FunctionResultContent("function result: 10")]);
        yield return new ChatMessageContent(AuthorRole.Assistant, "asistant response: 11");
        yield return new ChatMessageContent(AuthorRole.User, "user input: 12");
        yield return new ChatMessageContent(AuthorRole.Assistant, "asistant response: 13");
    }
}
