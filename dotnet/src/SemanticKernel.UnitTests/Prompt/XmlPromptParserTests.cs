// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Prompt;

/// <summary>
/// Unit tests for <see cref="XmlPromptParser"/> class.
/// </summary>
public class XmlPromptParserTests
{
    [Theory]
    [InlineData("This is plain prompt")]
    [InlineData("<message This is invalid chat prompt>")]
    public void ItReturnsNullListWhenPromptIsPlainText(string prompt)
    {
        // Act
        var result = XmlPromptParser.TryParse(prompt, out var nodes);

        // Assert
        Assert.False(result);
        Assert.Null(nodes);
    }

    [Fact]
    public void ItReturnsPromptNodesWhenPromptHasXmlFormat()
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

<message role='user'>
    <audio src='https://fake-link-to-audio' />
</message>
";

        var expectedNodes = new List<PromptNode>
        {
            new("message") { Attributes = { { "role", "system" } }, Content = "Test with role in double quotes and content in new line." },
            new("message") { Attributes = { { "role", "user" } }, Content = "Test with role in single quotes and content in the same line." },
            new("message") { Attributes = { { "role", "assistant" } }, Content = "Test with multiline content.\nSecond line." },
            new("message") { Attributes = { { "role", "system" } }, Content = "Test line with tab." },
            new("message")
            {
                Attributes = { { "role", "user" } },
                ChildNodes = new List<PromptNode> { new("audio") { Attributes = { { "src", "https://fake-link-to-audio" } } } }
            },
        };

        // Act
        var result = XmlPromptParser.TryParse(Prompt, out var actualNodes);

        // Assert
        Assert.True(result);
        Assert.NotNull(actualNodes);

        for (var i = 0; i < actualNodes.Count; i++)
        {
            this.AssertPromptNode(expectedNodes[i], actualNodes[i]);
        }
    }

    private void AssertPromptNode(PromptNode expectedNode, PromptNode actualNode)
    {
        Assert.Equal(expectedNode.TagName, expectedNode.TagName);
        Assert.Equal(expectedNode.Content, actualNode.Content);

        var attributeKeys = expectedNode.Attributes.Keys.ToArray();

        for (var i = 0; i < attributeKeys.Length; i++)
        {
            var key = attributeKeys[i];
            Assert.Equal(expectedNode.Attributes[key], actualNode.Attributes[key]);
        }

        for (var i = 0; i < expectedNode.ChildNodes.Count; i++)
        {
            this.AssertPromptNode(expectedNode.ChildNodes[i], actualNode.ChildNodes[i]);
        }
    }
}
