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
/// Unit testing of <see cref="ChatHistorySummarizationReducer"/>.
/// </summary>
public class ChatHistorySummarizationReducerTests
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
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();

        Assert.Throws<ArgumentException>(() => new ChatHistorySummarizationReducer(mockCompletionService.Object, targetCount, thresholdCount));
    }

    /// <summary>
    /// Verify object state after initialization.
    /// </summary>
    [Fact]
    public void VerifyChatHistoryInitializationState()
    {
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();

        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 10);

        Assert.Equal(ChatHistorySummarizationReducer.DefaultSummarizationPrompt, reducer.SummarizationInstructions);
        Assert.True(reducer.FailOnError);

        reducer =
            new(mockCompletionService.Object, 10)
            {
                FailOnError = false,
                SummarizationInstructions = "instructions",
            };

        Assert.NotEqual(ChatHistorySummarizationReducer.DefaultSummarizationPrompt, reducer.SummarizationInstructions);
        Assert.False(reducer.FailOnError);
    }

    /// <summary>
    /// Validate hash-code expresses reducer equivalency.
    /// </summary>
    [Fact]
    public void VerifyChatHistoryHasCode()
    {
        HashSet<ChatHistorySummarizationReducer> reducers = [];

        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();

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
            ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, targetCount, thresholdCount);

            reducers.Add(reducer);

            return reducer.GetHashCode();
        }
    }

    /// <summary>
    /// Validate silent summarization failure when <see cref="ChatHistorySummarizationReducer.FailOnError"/> set to 'false'.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryReductionSilentFailureAsync()
    {
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService(throwException: true);
        IReadOnlyList<ChatMessageContent> sourceHistory = MockHistoryGenerator.CreateSimpleHistory(20).ToArray();

        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 10) { FailOnError = false };
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        Assert.Null(reducedHistory);
    }

    /// <summary>
    /// Validate exception on summarization failure when <see cref="ChatHistorySummarizationReducer.FailOnError"/> set to 'true'.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryReductionThrowsOnFailureAsync()
    {
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService(throwException: true);
        IReadOnlyList<ChatMessageContent> sourceHistory = MockHistoryGenerator.CreateSimpleHistory(20).ToArray();

        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 10);
        await Assert.ThrowsAsync<HttpOperationException>(() => reducer.ReduceAsync(sourceHistory));
    }

    /// <summary>
    /// Validate history not reduced when source history does not exceed target threshold.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryNotReducedAsync()
    {
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();
        IReadOnlyList<ChatMessageContent> sourceHistory = MockHistoryGenerator.CreateSimpleHistory(20).ToArray();

        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 20);
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        Assert.Null(reducedHistory);
    }

    /// <summary>
    /// Validate history reduced when source history exceeds target threshold.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryReducedAsync()
    {
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();
        IReadOnlyList<ChatMessageContent> sourceHistory = MockHistoryGenerator.CreateSimpleHistory(20).ToArray();

        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 10);
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        ChatMessageContent[] messages = VerifyReducedHistory(reducedHistory, 11);
        VerifySummarization(messages[0]);
    }

    /// <summary>
    /// Validate history re-summarized on second occurrence of source history exceeding target threshold.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryRereducedAsync()
    {
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();
        IReadOnlyList<ChatMessageContent> sourceHistory = MockHistoryGenerator.CreateSimpleHistory(20).ToArray();

        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 10);
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);
        reducedHistory = await reducer.ReduceAsync([.. reducedHistory!, .. sourceHistory]);

        ChatMessageContent[] messages = VerifyReducedHistory(reducedHistory, 11);
        VerifySummarization(messages[0]);

        reducer = new(mockCompletionService.Object, 10) { UseSingleSummary = false };
        reducedHistory = await reducer.ReduceAsync([.. reducedHistory!, .. sourceHistory]);

        messages = VerifyReducedHistory(reducedHistory, 12);
        VerifySummarization(messages[0]);
        VerifySummarization(messages[1]);
    }

    private static ChatMessageContent[] VerifyReducedHistory(IEnumerable<ChatMessageContent>? reducedHistory, int expectedCount)
    {
        Assert.NotNull(reducedHistory);
        ChatMessageContent[] messages = reducedHistory.ToArray();
        Assert.Equal(expectedCount, messages.Length);

        return messages;
    }

    private static void VerifySummarization(ChatMessageContent message)
    {
        Assert.NotNull(message.Metadata);
        Assert.True(message.Metadata!.ContainsKey(ChatHistorySummarizationReducer.SummaryMetadataKey));
    }

    private Mock<IChatCompletionService> CreateMockCompletionService(bool throwException = false)
    {
        Mock<IChatCompletionService> mock = new();
        var setup = mock.Setup(
            s =>
                s.GetChatMessageContentsAsync(
                    It.IsAny<ChatHistory>(),
                    It.IsAny<PromptExecutionSettings>(),
                    It.IsAny<Kernel>(),
                    default));

        if (throwException)
        {
            setup.ThrowsAsync(new HttpOperationException("whoops"));
        }
        else
        {
            setup.ReturnsAsync([new(AuthorRole.Assistant, "summary")]);
        }

        return mock;
    }
}
