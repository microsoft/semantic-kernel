// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Internal;

/// <summary>
/// Unit testing of <see cref="AssistantMessageFactory"/>.
/// </summary>
public class AssistantMessageFactoryTests
{
    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterCreateOptionsDefault()
    {
        // Arrange (Setup message with null metadata)
        ChatMessageContent message = new(AuthorRole.User, "test");

        // Act: Create options
        MessageCreationOptions options = AssistantMessageFactory.CreateOptions(message);

        // Assert
        Assert.NotNull(options);
        Assert.Empty(options.Metadata);
    }

    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterCreateOptionsWithMetadataEmpty()
    {
        // Arrange Setup message with empty metadata
        ChatMessageContent message =
            new(AuthorRole.User, "test")
            {
                Metadata = new Dictionary<string, object?>()
            };

        // Act: Create options
        MessageCreationOptions options = AssistantMessageFactory.CreateOptions(message);

        // Assert
        Assert.NotNull(options);
        Assert.Empty(options.Metadata);
    }

    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterCreateOptionsWithMetadata()
    {
        // Arrange: Setup message with metadata
        ChatMessageContent message =
            new(AuthorRole.User, "test")
            {
                Metadata =
                    new Dictionary<string, object?>()
                    {
                        { "a", 1 },
                        { "b", "2" },
                    }
            };

        // Act: Create options
        MessageCreationOptions options = AssistantMessageFactory.CreateOptions(message);

        // Assert
        Assert.NotNull(options);
        Assert.NotEmpty(options.Metadata);
        Assert.Equal(2, options.Metadata.Count);
        Assert.Equal("1", options.Metadata["a"]);
        Assert.Equal("2", options.Metadata["b"]);
    }

    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterCreateOptionsWithMetadataNull()
    {
        // Arrange: Setup message with null metadata value
        ChatMessageContent message =
            new(AuthorRole.User, "test")
            {
                Metadata =
                    new Dictionary<string, object?>()
                    {
                        { "a", null },
                        { "b", "2" },
                    }
            };

        // Act: Create options
        MessageCreationOptions options = AssistantMessageFactory.CreateOptions(message);

        // Assert
        Assert.NotNull(options);
        Assert.NotEmpty(options.Metadata);
        Assert.Equal(2, options.Metadata.Count);
        Assert.Equal(string.Empty, options.Metadata["a"]);
        Assert.Equal("2", options.Metadata["b"]);
    }

    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterGetMessageContentsWithText()
    {
        // Arrange
        ChatMessageContent message = new(AuthorRole.User, items: [new TextContent("test")]);

        // Act
        MessageContent[] contents = AssistantMessageFactory.GetMessageContents(message).ToArray();

        // Assert
        Assert.NotNull(contents);
        Assert.Single(contents);
        Assert.NotNull(contents.Single().Text);
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
        MessageContent[] contents = AssistantMessageFactory.GetMessageContents(message).ToArray();

        // Assert
        Assert.NotNull(contents);
        Assert.Single(contents);
        Assert.NotNull(contents.Single().ImageUri);
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
        MessageContent[] contents = AssistantMessageFactory.GetMessageContents(message).ToArray();

        // Assert
        Assert.NotNull(contents);
        Assert.Single(contents);
        Assert.NotNull(contents.Single().ImageUri);
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
        MessageContent[] contents = AssistantMessageFactory.GetMessageContents(message).ToArray();

        // Assert
        Assert.NotNull(contents);
        Assert.Single(contents);
        Assert.NotNull(contents.Single().ImageFileId);
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
        MessageContent[] contents = AssistantMessageFactory.GetMessageContents(message).ToArray();

        // Assert
        Assert.NotNull(contents);
        Assert.Equal(3, contents.Length);
    }
}
