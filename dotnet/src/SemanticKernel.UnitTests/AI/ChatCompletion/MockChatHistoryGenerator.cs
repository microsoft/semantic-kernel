// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace SemanticKernel.UnitTests.AI.ChatCompletion;

/// <summary>
/// Factory for generating chat history for various test scenarios.
/// </summary>
internal static class MockChatHistoryGenerator
{
    /// <summary>
    /// Create a homogeneous list of assistant messages.
    /// </summary>
    public static IEnumerable<ChatMessageContent> CreateSimpleHistory(int messageCount, bool includeSystemMessage = false)
    {
        if (includeSystemMessage)
        {
            yield return new ChatMessageContent(AuthorRole.System, "system message");
        }

        for (int index = 0; index < messageCount; ++index)
        {
            yield return new ChatMessageContent(AuthorRole.Assistant, $"message #{index}");
        }
    }

    /// <summary>
    /// Create an alternating list of user and assistant messages.
    /// </summary>
    public static IEnumerable<ChatMessageContent> CreateHistoryWithUserInput(int messageCount)
    {
        for (int index = 0; index < messageCount; ++index)
        {
            yield return
                index % 2 == 1 ?
                    new ChatMessageContent(AuthorRole.Assistant, $"assistant response: {index}") :
                    new ChatMessageContent(AuthorRole.User, $"user input: {index}");
        }
    }

    /// <summary>
    /// Create an alternating list of user and assistant messages with function content
    /// injected at indexes:
    ///
    /// - 5: function call
    /// - 6: function result
    /// - 9: function call
    /// - 10: function result
    ///
    /// Total message count: 14 messages.
    /// </summary>
    public static IEnumerable<ChatMessageContent> CreateHistoryWithFunctionContent()
    {
        yield return new ChatMessageContent(AuthorRole.User, "user input: 0");
        yield return new ChatMessageContent(AuthorRole.Assistant, "assistant response: 1");
        yield return new ChatMessageContent(AuthorRole.User, "user input: 2");
        yield return new ChatMessageContent(AuthorRole.Assistant, "assistant response: 3");
        yield return new ChatMessageContent(AuthorRole.User, "user input: 4");
        yield return new ChatMessageContent(AuthorRole.Assistant, [new FunctionCallContent("function call: 5")]);
        yield return new ChatMessageContent(AuthorRole.Tool, [new FunctionResultContent("function result: 6")]);
        yield return new ChatMessageContent(AuthorRole.Assistant, "assistant response: 7");
        yield return new ChatMessageContent(AuthorRole.User, "user input: 8");
        yield return new ChatMessageContent(AuthorRole.Assistant, [new FunctionCallContent("function call: 9")]);
        yield return new ChatMessageContent(AuthorRole.Tool, [new FunctionResultContent("function result: 10")]);
        yield return new ChatMessageContent(AuthorRole.Assistant, "assistant response: 11");
        yield return new ChatMessageContent(AuthorRole.User, "user input: 12");
        yield return new ChatMessageContent(AuthorRole.Assistant, "assistant response: 13");
    }
}
