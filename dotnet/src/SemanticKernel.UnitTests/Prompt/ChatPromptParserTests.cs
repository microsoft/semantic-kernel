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
    [InlineData("<message role='user'><text>This is an invalid chat prompt</message></text>")]
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

    [Fact]
    public void ItReturnsChatHistoryWithValidContentItemsIncludeCData()
    {
        // Arrange
        string prompt = GetValidPromptWithCDataSection();

        // Act
        bool result = ChatPromptParser.TryParse(prompt, out var chatHistory);

        // Assert
        Assert.True(result);
        Assert.NotNull(chatHistory);

        Assert.Collection(chatHistory,
            c => Assert.Equal("""
                              <message role='system'><text>Text content</text></message>
                              """, c.Content),
            c => Assert.Equal("""
                              <text>explain image</text>
                              <image>https://fake-link-to-image/</image>
                              """, c.Content));
    }

    [Fact]
    public void ItReturnsChatHistoryWithValidDataImageContent()
    {
        // Arrange
        string prompt = GetValidPromptWithDataUriImageContent();

        // Act
        bool result = ChatPromptParser.TryParse(prompt, out var chatHistory);

        // Assert
        Assert.True(result);
        Assert.NotNull(chatHistory);

        Assert.Collection(chatHistory,
            c => Assert.Equal("What can I help with?", c.Content),
            c =>
            {
                Assert.Equal("Explain this image", c.Content);
                Assert.Collection(c.Items,
                    o =>
                    {
                        Assert.IsType<TextContent>(o);
                        Assert.Equal("Explain this image", ((TextContent)o).Text);
                    },
                    o =>
                    {
                        Assert.IsType<ImageContent>(o);
                        Assert.Equal("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAACVJREFUKFNj/KTO/J+BCMA4iBUyQX1A0I10VAizCj1oMdyISyEAFoQbHwTcuS8AAAAASUVORK5CYII=", ((ImageContent)o).DataUri);
                        Assert.Equal("image/png", ((ImageContent)o).MimeType);
                        Assert.NotNull(((ImageContent)o).Data);
                    });
            });
    }

    [Fact]
    public void ItReturnsChatHistoryWithMultipleTextParts()
    {
        // Arrange
        string prompt = GetValidPromptWithMultipleTextParts();

        // Act
        bool result = ChatPromptParser.TryParse(prompt, out var chatHistory);

        // Assert
        Assert.True(result);
        Assert.NotNull(chatHistory);

        Assert.Collection(chatHistory,
            c => Assert.Equal("What can I help with?", c.Content),
            c =>
            {
                Assert.Equal("Hello", c.Content);
                Assert.Collection(c.Items,
                    o =>
                    {
                        Assert.IsType<TextContent>(o);
                        Assert.Equal("Hello", ((TextContent)o).Text);
                    }, o =>
                    {
                        Assert.IsType<TextContent>(o);
                        Assert.Equal("I am user", ((TextContent)o).Text);
                    });
            });
    }

    [Fact]
    public void ItReturnsChatHistoryWithMixedXmlContent()
    {
        // Arrange
        string prompt = GetValidPromptWithMixedXmlContent();

        // Act
        bool result = ChatPromptParser.TryParse(prompt, out var chatHistory);

        // Assert
        Assert.True(result);
        Assert.NotNull(chatHistory);

        Assert.Collection(chatHistory,
            c => Assert.Equal("What can I help with?", c.Content),
            c =>
            {
                Assert.Equal("Hi how are you?", c.Content);
                Assert.Single(c.Items);
            });
    }

    [Fact]
    public void ItReturnsChatHistoryWithEmptyContent()
    {
        // Arrange
        string prompt = GetValidPromptWithEmptyContent();

        // Act
        bool result = ChatPromptParser.TryParse(prompt, out var chatHistory);

        // Assert
        Assert.True(result);
        Assert.NotNull(chatHistory);

        Assert.Collection(chatHistory,
            c => Assert.Equal("What can I help with?", c.Content),
            c =>
            {
                Assert.Null(c.Content);
                Assert.Empty(c.Items);
            },
            c =>
            {
                Assert.Null(c.Content);
                Assert.Empty(c.Items);
            });
    }

    [Fact]
    public void ItReturnsChatHistoryWithValidContentItemsIncludeCode()
    {
        // Arrange
        string prompt = GetValidPromptWithCodeBlock();

        // Act
        bool result = ChatPromptParser.TryParse(prompt, out var chatHistory);

        // Assert
        Assert.True(result);
        Assert.NotNull(chatHistory);

        Assert.Collection(chatHistory,
            // The first message entry inside prompt is neither wrapped in CDATA or HtmlEncoded, so the single quotes are not preserved.
            c => Assert.Equal("""
                              <code>
                                  <message role="system">
                                      <text>Text content</text>
                                  </message>
                              </code>
                              """, c.Content),
            // Since the second message entry inside prompt is wrapped in CDATA, the single quotes are preserved.
            c => Assert.Equal("""
                              <code>
                                  <message role='system'>
                                      <text>Text content</text>
                                  </message>
                              </code>
                              """, c.Content),
             // Since the third message entry inside prompt is HtmlEncoded, the single quotes are preserved.
             c => Assert.Equal("""
                              <code>
                                  <message role='system'>
                                      <text>Text content</text>
                                  </message>
                              </code>
                              """, c.Content),
            // In this case, when we trim node.InnerXml only the opening <code> tag is indented. 
            c => Assert.Equal("""
                              <code>
                                  <text>explain image</text>
                                  <image>
                                    https://fake-link-to-image/
                                  </image>
                                </code>
                              """, c.Content));
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

    private static string GetValidPromptWithDataUriImageContent()
    {
        return
            """

            <message role="assistant">What can I help with?</message>

            <message role='user'>
                <text>Explain this image</text>
                <image>data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAACVJREFUKFNj/KTO/J+BCMA4iBUyQX1A0I10VAizCj1oMdyISyEAFoQbHwTcuS8AAAAASUVORK5CYII=</image>
            </message>

            """;
    }

    private static string GetValidPromptWithMultipleTextParts()
    {
        return
            """

            <message role="assistant">What can I help with?</message>

            <message role='user'>
                <text>Hello</text>
                <text>I am user</text>
            </message>

            """;
    }

    private static string GetValidPromptWithMixedXmlContent()
    {
        return
            """

            <message role="assistant">What can I help with?</message>

            <message role='user'>
                This part will be discarded upon parsing
                <text>Hi how are you?</text>
                This part will also be discarded upon parsing
            </message>

            """;
    }

    private static string GetValidPromptWithEmptyContent()
    {
        return
            """

            <message role="assistant">What can I help with?</message>
            <message role='user'/>
            <message role='user'>
            </message>

            """;
    }

    private static string GetValidPromptWithCDataSection()
    {
        return
            """

            <message role="assistant">
            <![CDATA[
            <message role='system'><text>Text content</text></message>
            ]]>
            </message>

            <message role='user'>
            <![CDATA[
            <text>explain image</text>
            <image>https://fake-link-to-image/</image>
            ]]>
            </message>

            """;
    }

    private static string GetValidPromptWithCodeBlock()
    {
        return
            """

            <message role="assistant">
            <code>
                <message role='system'>
                    <text>Text content</text>
                </message>
            </code>
            </message>

            <message role="assistant">
            <![CDATA[
            <code>
                <message role='system'>
                    <text>Text content</text>
                </message>
            </code>
            ]]>
            </message>

            <message role="assistant">
            &lt;code&gt;
                &lt;message role=&#39;system&#39;&gt;
                    &lt;text&gt;Text content&lt;/text&gt;
                &lt;/message&gt;
            &lt;/code&gt;
            </message>

            <message role='user'>
              <code>
                <text>explain image</text>
                <image>
                  https://fake-link-to-image/
                </image>
              </code>
            </message>

            """;
    }
}
