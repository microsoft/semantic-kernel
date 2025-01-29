// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// Unit tests for <see cref="IChatHistoryReducer"/> implementations.
/// </summary>
public class ChatHistoryReducerTests(ITestOutputHelper output) : BaseTest(output)
{
    [Theory]
    [InlineData(3, null, null, 100, 0)]
    [InlineData(3, "SystemMessage", null, 100, 0)]
    [InlineData(6, null, null, 100, 4)]
    [InlineData(6, "SystemMessage", null, 100, 5)]
    [InlineData(6, null, new int[] { 1 }, 100, 4)]
    [InlineData(6, "SystemMessage", new int[] { 2 }, 100, 4)]
    public async Task VerifyMaxTokensChatHistoryReducerAsync(int messageCount, string? systemMessage, int[]? functionCallIndexes, int maxTokens, int expectedSize)
    {
        // Arrange
        var chatHistory = CreateHistoryWithUserInput(messageCount, systemMessage, functionCallIndexes, true);
        var reducer = new ChatHistoryMaxTokensReducer(maxTokens);

        // Act
        var reducedHistory = await reducer.ReduceAsync(chatHistory);

        // Assert
        VerifyReducedHistory(reducedHistory, ComputeExpectedMessages(chatHistory, expectedSize));
    }

    private static void VerifyReducedHistory(IEnumerable<ChatMessageContent>? reducedHistory, ChatMessageContent[]? expectedMessages)
    {
        if (expectedMessages is null)
        {
            Assert.Null(reducedHistory);
            return;
        }
        Assert.NotNull(reducedHistory);
        ChatMessageContent[] messages = reducedHistory.ToArray();
        Assert.Equal(expectedMessages.Length, messages.Length);
        Assert.Equal(expectedMessages, messages);
    }

    private static ChatMessageContent[]? ComputeExpectedMessages(ChatHistory chatHistory, int expectedSize)
    {
        if (expectedSize == 0)
        {
            return null;
        }

        var systemMessage = chatHistory.GetSystemMessage();
        var count = expectedSize - ((systemMessage is null) ? 0 : 1);
        var expectedMessages = chatHistory.TakeLast<ChatMessageContent>(count).ToArray();
        if (systemMessage is not null)
        {
            expectedMessages = [systemMessage, .. expectedMessages];
        }
        return expectedMessages;
    }

    /// <summary>
    /// Create an alternating list of user and assistant messages.
    /// Function content is optionally injected at specified indexes.
    /// </summary>
    private static ChatHistory CreateHistoryWithUserInput(int messageCount, string? systemMessage = null, int[]? functionCallIndexes = null, bool includeTokenCount = false)
    {
        var text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.";
        var chatHistory = new ChatHistory();
        if (systemMessage is not null)
        {
            chatHistory.AddSystemMessageWithTokenCount(systemMessage);
        }
        for (int index = 0; index < messageCount; ++index)
        {
            if (index % 2 == 1)
            {
                if (includeTokenCount)
                {
                    chatHistory.AddAssistantMessageWithTokenCount($"Assistant response:{index}  - {text}");
                }
                else
                {
                    chatHistory.AddAssistantMessage($"Assistant response:{index}  - {text}");
                }
            }
            else
            {
                if (includeTokenCount)
                {
                    chatHistory.AddUserMessageWithTokenCount($"User input:{index}  - {text}");
                }
                else
                {
                    chatHistory.AddUserMessageWithTokenCount($"User input:{index}  - {text}");
                }
            }

            if (functionCallIndexes is not null && functionCallIndexes.Contains(index))
            {
                IReadOnlyDictionary<string, object?> metadata = new Dictionary<string, object?>
                {
                    ["TokenCount"] = 10
                };

                chatHistory.Add(new ChatMessageContent(AuthorRole.Assistant, [new FunctionCallContent($"Function call 1: {index}")], metadata: metadata));
                chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, [new FunctionResultContent($"Function call 1: {index}")], metadata: metadata));
                chatHistory.Add(new ChatMessageContent(AuthorRole.Assistant, [new FunctionCallContent($"Function call 2: {index}")], metadata: metadata));
                chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, [new FunctionResultContent($"Function call 2: {index}")], metadata: metadata));
            }
        }
        return chatHistory;
    }

    private sealed class FakeChatCompletionService(string result) : IChatCompletionService
    {
        public IReadOnlyDictionary<string, object?> Attributes { get; } = new Dictionary<string, object?>();

        public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<ChatMessageContent>>([new(AuthorRole.Assistant, result)]);
        }

#pragma warning disable IDE0036 // Order modifiers
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
#pragma warning restore IDE0036 // Order modifiers
        {
            yield return new StreamingChatMessageContent(AuthorRole.Assistant, result);
        }
    }
}
