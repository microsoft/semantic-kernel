// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Linq;
using Azure.AI.Agents.Persistent;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI.Internal;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.AzureAI.Internal;

/// <summary>
/// Unit testing of <see cref="AgentMessageFactory"/>.
/// </summary>
public class AgentMessageFactoryTests
{
    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterGetMessageContentsWithText()
    {
        // Arrange
        ChatMessageContent message = new(AuthorRole.User, items: [new TextContent("test")]);

        // Act
        ThreadMessageOptions[] contents = AgentMessageFactory.GetThreadMessages([message]).ToArray();

        // Assert
        Assert.NotNull(contents);
        Assert.Single(contents);
        Assert.NotNull(contents[0].Content);
    }

    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterGetMessageWithImageUrl()
    {
        // Arrange
        ChatMessageContent message = new(AuthorRole.User, items: [new ImageContent(new Uri("https://localhost/myimage.png"))]);

        // Act
        ThreadMessageOptions[] contents = AgentMessageFactory.GetThreadMessages([message]).ToArray();

        // Assert
        Assert.NotNull(contents);
        Assert.Empty(contents);
    }

    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterGetMessageWithImageData()
    {
        // Arrange
        ChatMessageContent message = new(AuthorRole.User, items: [new ImageContent(new byte[] { 1, 2, 3 }, "image/png") { DataUri = "data:image/png;base64,MTIz" }]);

        // Act
        ThreadMessageOptions[] contents = AgentMessageFactory.GetThreadMessages([message]).ToArray();

        // Assert
        Assert.NotNull(contents);
        Assert.Empty(contents);
    }

    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterGetMessageWithImageFile()
    {
        // Arrange
        ChatMessageContent message = new(AuthorRole.User, items: [new FileReferenceContent("file-id")]);

        // Act
        ThreadMessageOptions[] contents = AgentMessageFactory.GetThreadMessages([message]).ToArray();

        // Assert
        Assert.NotNull(contents);
        Assert.Empty(contents);
    }

    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterGetMessageWithAll()
    {
        // Arrange
        ChatMessageContent message =
            new(
                AuthorRole.User,
                items:
                [
                    new TextContent("test"),
                    new ImageContent(new Uri("https://localhost/myimage.png")),
                    new FileReferenceContent("file-id")
                ]);

        // Act
        ThreadMessageOptions[] contents = AgentMessageFactory.GetThreadMessages([message]).ToArray();

        // Assert
        Assert.NotNull(contents);
        Assert.Single(contents);
        Assert.NotNull(contents[0].Content);
        Assert.Single(contents[0].Attachments);
    }
}
