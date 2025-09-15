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
    public void VerifyConstructorArgumentValidation(int targetCount, int? thresholdCount = null)
    {
        // Arrange
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();

        // Act & Assert
        Assert.Throws<ArgumentException>(() => new ChatHistorySummarizationReducer(mockCompletionService.Object, targetCount, thresholdCount));
    }

    /// <summary>
    /// Verify object state after initialization.
    /// </summary>
    [Fact]
    public void VerifyInitializationState()
    {
        // Arrange
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();
        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 10);

        // Assert
        Assert.Equal(ChatHistorySummarizationReducer.DefaultSummarizationPrompt, reducer.SummarizationInstructions);
        Assert.True(reducer.FailOnError);

        // Act
        reducer =
            new(mockCompletionService.Object, 10)
            {
                FailOnError = false,
                SummarizationInstructions = "instructions",
            };

        // Assert
        Assert.NotEqual(ChatHistorySummarizationReducer.DefaultSummarizationPrompt, reducer.SummarizationInstructions);
        Assert.False(reducer.FailOnError);
    }

    /// <summary>
    /// Validate equality override.
    /// </summary>
    [Fact]
    public void VerifyEquality()
    {
        // Arrange
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();

        ChatHistorySummarizationReducer reducer1 = new(mockCompletionService.Object, 3, 3);
        ChatHistorySummarizationReducer reducer2 = new(mockCompletionService.Object, 3, 3);
        ChatHistorySummarizationReducer reducer3 = new(mockCompletionService.Object, 3, 3) { UseSingleSummary = false };
        ChatHistorySummarizationReducer reducer4 = new(mockCompletionService.Object, 3, 3) { SummarizationInstructions = "override" };
        ChatHistorySummarizationReducer reducer5 = new(mockCompletionService.Object, 4, 3);
        ChatHistorySummarizationReducer reducer6 = new(mockCompletionService.Object, 3, 5);
        ChatHistorySummarizationReducer reducer7 = new(mockCompletionService.Object, 3);
        ChatHistorySummarizationReducer reducer8 = new(mockCompletionService.Object, 3);

        // Assert
        Assert.True(reducer1.Equals(reducer1));
        Assert.True(reducer1.Equals(reducer2));
        Assert.True(reducer7.Equals(reducer8));
        Assert.True(reducer3.Equals(reducer3));
        Assert.True(reducer4.Equals(reducer4));
        Assert.False(reducer1.Equals(reducer3));
        Assert.False(reducer1.Equals(reducer4));
        Assert.False(reducer1.Equals(reducer5));
        Assert.False(reducer1.Equals(reducer6));
        Assert.False(reducer1.Equals(reducer7));
        Assert.False(reducer1.Equals(reducer8));
        Assert.False(reducer1.Equals(null));
    }

    /// <summary>
    /// Validate hash-code expresses reducer equivalency.
    /// </summary>
    [Fact]
    public void VerifyHashCode()
    {
        // Arrange
        HashSet<ChatHistorySummarizationReducer> reducers = [];

        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();

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
        // Arrange
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService(throwException: true);
        IReadOnlyList<ChatMessageContent> sourceHistory = MockChatHistoryGenerator.CreateSimpleHistory(20).ToArray();
        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 10) { FailOnError = false };

        // Act
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        // Assert
        Assert.Null(reducedHistory);
    }

    /// <summary>
    /// Validate exception on summarization failure when <see cref="ChatHistorySummarizationReducer.FailOnError"/> set to 'true'.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryReductionThrowsOnFailureAsync()
    {
        // Arrange
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService(throwException: true);
        IReadOnlyList<ChatMessageContent> sourceHistory = MockChatHistoryGenerator.CreateSimpleHistory(20).ToArray();
        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 10);

        // Act and Assert
        await Assert.ThrowsAsync<HttpOperationException>(() => reducer.ReduceAsync(sourceHistory));
    }

    /// <summary>
    /// Validate history not reduced when source history does not exceed target threshold.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryNotReducedAsync()
    {
        // Arrange
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();
        IReadOnlyList<ChatMessageContent> sourceHistory = MockChatHistoryGenerator.CreateSimpleHistory(20).ToArray();
        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 20);

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
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();
        IReadOnlyList<ChatMessageContent> sourceHistory = MockChatHistoryGenerator.CreateSimpleHistory(20).ToArray();
        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 10);

        // Act
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        // Assert
        ChatMessageContent[] messages = VerifyReducedHistory(reducedHistory, 11);
        VerifySummarization(messages[0]);
    }

    /// <summary>
    /// Validate history re-summarized on second occurrence of source history exceeding target threshold.
    /// </summary>
    [Fact]
    public async Task VerifyChatHistoryRereducedAsync()
    {
        // Arrange
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();
        IReadOnlyList<ChatMessageContent> sourceHistory = MockChatHistoryGenerator.CreateSimpleHistory(20).ToArray();
        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 10);

        // Act
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);
        reducedHistory = await reducer.ReduceAsync([.. reducedHistory!, .. sourceHistory]);

        // Assert
        ChatMessageContent[] messages = VerifyReducedHistory(reducedHistory, 11);
        VerifySummarization(messages[0]);

        // Act
        reducer = new(mockCompletionService.Object, 10) { UseSingleSummary = false };
        reducedHistory = await reducer.ReduceAsync([.. reducedHistory!, .. sourceHistory]);

        // Assert
        messages = VerifyReducedHistory(reducedHistory, 12);
        VerifySummarization(messages[0]);
        VerifySummarization(messages[1]);
    }

    /// <summary>
    /// Validate history reduced and system message preserved when source history exceeds target threshold.
    /// </summary>
    [Fact]
    public async Task VerifySystemMessageIsNotReducedAsync()
    {
        // Arrange
        Mock<IChatCompletionService> mockCompletionService = this.CreateMockCompletionService();
        IReadOnlyList<ChatMessageContent> sourceHistory = MockChatHistoryGenerator.CreateSimpleHistory(20, includeSystemMessage: true).ToArray();
        ChatHistorySummarizationReducer reducer = new(mockCompletionService.Object, 10);

        // Act
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(sourceHistory);

        // Assert
        ChatMessageContent[] messages = VerifyReducedHistory(reducedHistory, 11);
        VerifySummarization(messages[1]);

        Assert.Contains(messages, m => m.Role == AuthorRole.System);
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
