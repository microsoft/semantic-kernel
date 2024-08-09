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
        // Setup message with null metadata
        ChatMessageContent message = new(AuthorRole.User, "test");

        // Act
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
        // Setup message with empty metadata
        ChatMessageContent message =
            new(AuthorRole.User, "test")
            {
                Metadata = new Dictionary<string, object?>()
            };

        // Create options
        MessageCreationOptions options = AssistantMessageFactory.CreateOptions(message);

        // Validate
        Assert.NotNull(options);
        Assert.Empty(options.Metadata);
    }

    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterCreateOptionsWithMetadata()
    {
        // Setup message with metadata
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

        // Create options
        MessageCreationOptions options = AssistantMessageFactory.CreateOptions(message);

        // Validate
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
        // Setup message with null metadata value
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

        // Create options
        MessageCreationOptions options = AssistantMessageFactory.CreateOptions(message);

        // Validate
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
        ChatMessageContent message = new(AuthorRole.User, items: [new TextContent("test")]);
        MessageContent[] contents = AssistantMessageFactory.GetMessageContents(message).ToArray();
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
        ChatMessageContent message = new(AuthorRole.User, items: [new ImageContent(new Uri("https://localhost/myimage.png"))]);
        MessageContent[] contents = AssistantMessageFactory.GetMessageContents(message).ToArray();
        Assert.NotNull(contents);
        Assert.Single(contents);
        Assert.NotNull(contents.Single().ImageUrl);
    }

    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact(Skip = "API bug with data Uri construction")]
    public void VerifyAssistantMessageAdapterGetMessageWithImageData()
    {
        ChatMessageContent message = new(AuthorRole.User, items: [new ImageContent(new byte[] { 1, 2, 3 }, "image/png")]);
        MessageContent[] contents = AssistantMessageFactory.GetMessageContents(message).ToArray();
        Assert.NotNull(contents);
        Assert.Single(contents);
        Assert.NotNull(contents.Single().ImageUrl);
    }

    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterGetMessageWithImageFile()
    {
        ChatMessageContent message = new(AuthorRole.User, items: [new FileReferenceContent("file-id")]);
        MessageContent[] contents = AssistantMessageFactory.GetMessageContents(message).ToArray();
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
        ChatMessageContent message =
            new(
                AuthorRole.User,
                items:
                [
                    new TextContent("test"),
                    new ImageContent(new Uri("https://localhost/myimage.png")),
                    new FileReferenceContent("file-id")
                ]);
        MessageContent[] contents = AssistantMessageFactory.GetMessageContents(message).ToArray();
        Assert.NotNull(contents);
        Assert.Equal(3, contents.Length);
    }
}
