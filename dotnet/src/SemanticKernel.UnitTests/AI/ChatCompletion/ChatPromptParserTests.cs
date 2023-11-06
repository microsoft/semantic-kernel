// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.AI.ChatCompletion;

/// <summary>
/// Unit tests for <see cref="ChatPromptParser"/> class.
/// </summary>
public class ChatPromptParserTests
{
    [Theory]
    [InlineData("This is plain prompt", false)]
    [InlineData("<message>This is not completed chat prompt</message>", false)]
    [InlineData("<message role=\"system\">This is completed chat prompt</message>", true)]
    [InlineData("<message role=\"system\">System message</message><message role=\"user\">User message</message>", true)]
    public void ChatPromptIdentificationWorksCorrectly(string prompt, bool expectedResult)
    {
        Assert.Equal(expectedResult, ChatPromptParser.TryGetChatHistory(prompt, out _));
    }

    [Theory]
    [InlineData("This is plain prompt", null)]
    [InlineData("<message>This is not completed chat prompt</message>", null)]
    public void ItReturnsNullChatHistoryWhenPromptIsNotChatPrompt(string prompt, ChatHistory? expectedChatHistory)
    {
        // Act
        var result = ChatPromptParser.TryGetChatHistory(prompt, out var chatHistory);

        // Assert
        Assert.False(result);
        Assert.Equal(expectedChatHistory, chatHistory);
    }

    [Fact]
    public void ItReturnsChatHistoryWhenPromptIsChatPrompt()
    {
        // Arrange
        const string Prompt = @"
<message role=""system"">
Test with role in double quotes and content in new line.
</message>

<message role='user'>Test with role in single quotes and content in the same line.</message>

<message role=""assistant"">
Test with multiline content.
Second line.
</message>

<message role='system'>
    Test line with tab.
</message>
";

        var expectedChatHistory = new ChatHistory();
        expectedChatHistory.AddSystemMessage("Test with role in double quotes and content in new line.");
        expectedChatHistory.AddUserMessage("Test with role in single quotes and content in the same line.");
        expectedChatHistory.AddAssistantMessage("Test with multiline content.\nSecond line.");
        expectedChatHistory.AddSystemMessage("Test line with tab.");

        // Act
        var result = ChatPromptParser.TryGetChatHistory(Prompt, out var actualChatHistory);

        // Assert
        Assert.True(result);
        Assert.NotNull(actualChatHistory);

        for (var i = 0; i < expectedChatHistory.Count; i++)
        {
            this.AssertChatMessage(expectedChatHistory[i], actualChatHistory[i]);
        }
    }

    private void AssertChatMessage(ChatMessageBase expectedMessage, ChatMessageBase actualMessage)
    {
        Assert.Equal(expectedMessage.Role, actualMessage.Role);
        Assert.Equal(expectedMessage.Content, actualMessage.Content);
    }
}
