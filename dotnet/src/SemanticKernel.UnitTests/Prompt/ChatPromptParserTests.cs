// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.Prompt;

public sealed class ChatPromptParserTests
{
    [Theory]
    [InlineData("This is plain prompt")]
    [InlineData("<message This is invalid chat prompt>")]
    [InlineData("<message role='user'><text>This is invalid</text><text>chat prompt</text></message>")]
    public void ItReturnsNullChatHistoryWhenPromptIsPlainTextOrInvalid(string prompt)
    {
        // Act
        var result = ChatPromptParser.TryParse(prompt, out var chatHistory);

        // Assert
        Assert.False(result);
        Assert.Null(chatHistory);
    }

    [Fact]
    public void ItReturnsChatHistoryWithValidRolesWhenPromptIsValid()
    {
        // Arrange
        string prompt = GetSimpleValidPrompt();

        // Act
        bool result = ChatPromptParser.TryParse(prompt, out var chatHistory);

        // Assert
        Assert.True(result);
        Assert.NotNull(chatHistory);

        Assert.Collection(chatHistory,
            c => c.Role = AuthorRole.System,
            c => c.Role = AuthorRole.User,
            c => c.Role = AuthorRole.Assistant,
            c => c.Role = AuthorRole.System,
            c => c.Role = AuthorRole.User);
    }

    [Fact]
    public void ItReturnsChatHistoryWithValidContentWhenSimplePrompt()
    {
        // Arrange
        string prompt = GetSimpleValidPrompt();

        // Act
        bool result = ChatPromptParser.TryParse(prompt, out var chatHistory);

        // Assert
        Assert.True(result);
        Assert.NotNull(chatHistory);

        Assert.Collection(chatHistory,
            c => Assert.Equal("Test with role in double quotes and content in new line.", c.Content),
            c => Assert.Equal("Test with role in single quotes and content in the same line.", c.Content),
            c => Assert.Equal("""
                              Test with multiline content.
                              Second line.
                              """, c.Content),
            c => Assert.Equal("Test line with tab.", c.Content),
            c => Assert.Equal("Hello, I'm a user.", c.Content));
    }

    [Fact]
    public void ItReturnsChatHistoryWithValidContentItemsWhenNestedPrompt()
    {
        // Arrange
        string prompt = GetNestedItemsValidPrompt();

        // Act
        bool result = ChatPromptParser.TryParse(prompt, out var chatHistory);

        // Assert
        Assert.True(result);
        Assert.NotNull(chatHistory);

        Assert.Collection(chatHistory,
            c => Assert.Equal("Hi how are you?", c.Content),
            c => Assert.Equal("""
                              Test with multiline content.
                              Second line.
                              """, c.Content),
            c => Assert.True(((TextContent)c.Items![0]).Text!.Equals("explain image", StringComparison.Ordinal)
                             && ((ImageContent)c.Items![1]).Uri!.AbsoluteUri == "https://fake-link-to-image/"));
    }

    private static string GetSimpleValidPrompt()
    {
        return
            """

            <message role="system">
            Test with role in double quotes and content in new line.
            </message>

            <message role='user'>Test with role in single quotes and content in the same line.</message>

            <message role="assistant">
            Test with multiline content.
            Second line.
            </message>

            <message role='system'>
                Test line with tab.
            </message>

            <message role='user'>
                Hello, I'm a user.
            </message>

            """;
    }

    private static string GetNestedItemsValidPrompt()
    {
        return
            """

            <message role='user'><text>Hi how are you?</text></message>

            <message role="assistant">
            Test with multiline content.
            Second line.
            </message>

            <message role='user'>
                <text>explain image</text>
                <image>https://fake-link-to-image/</image>
            </message>

            """;
    }
}
