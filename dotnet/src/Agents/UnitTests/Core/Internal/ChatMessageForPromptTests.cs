// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Internal;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Internal;

/// <summary>
/// Unit testing of <see cref="ChatMessageForPrompt"/>.
/// </summary>
public class ChatMessageForPromptTests
{
    /// <summary>
    /// Verify <see cref="ChatMessageForPrompt"/> formats history for prompt.
    /// </summary>
    [Fact]
    public void VerifyFormatHistoryAsync()
    {
        // Arrange & Act
        string history = ChatMessageForPrompt.Format([]);
        // Assert
        VerifyMessageCount<ChatMessageForTest>(history, 0);

        // Arrange & Act
        history = ChatMessageForPrompt.Format(CreatHistory());
        // Assert
        ChatMessageForTest[] messages = VerifyMessageCount<ChatMessageForTest>(history, 4);
        Assert.Equal("test", messages[1].Name);
        Assert.Equal(string.Empty, messages[2].Name);
        Assert.Equal("test", messages[3].Name);
    }

    /// <summary>
    /// Verify <see cref="ChatMessageForPrompt"/> formats history using name only.
    /// </summary>
    [Fact]
    public void VerifyFormatNamesAsync()
    {
        // Arrange & Act
        string history = ChatMessageForPrompt.Format([], useNameOnly: true);
        // Assert
        VerifyMessageCount<string>(history, 0);

        // Arrange & Act
        history = ChatMessageForPrompt.Format(CreatHistory(), useNameOnly: true);
        // Assert
        string[] names = VerifyMessageCount<string>(history, 4);
        Assert.Equal("test", names[1]);
        Assert.Equal(AuthorRole.Assistant.Label, names[2]);
        Assert.Equal("test", names[3]);
    }

    private static TResult[] VerifyMessageCount<TResult>(string history, int expectedLength)
    {
        TResult[]? messages = JsonSerializer.Deserialize<TResult[]>(history);
        Assert.NotNull(messages);
        Assert.Equal(expectedLength, messages.Length);
        return messages;
    }

    private static ChatHistory CreatHistory()
    {
        return
            [
                new ChatMessageContent(AuthorRole.User, "content1"),
                new ChatMessageContent(AuthorRole.Assistant, "content1") { AuthorName = "test" },
                new ChatMessageContent(AuthorRole.Assistant, "content1"),
                new ChatMessageContent(AuthorRole.Assistant, "content1") { AuthorName = "test" },
            ];
    }

    private sealed class ChatMessageForTest
    {
        public string Role { get; init; } = string.Empty;

        public string? Name { get; init; } = string.Empty;

        public string Content { get; init; } = string.Empty;
    }
}
