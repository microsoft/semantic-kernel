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
/// Unit testing of <see cref="AssistantMessageAdapter"/>.
/// </summary>
public class AssistantMessageAdapterTests
{
    /// <summary>
    /// Verify options creation.
    /// </summary>
    [Fact]
    public void VerifyAssistantMessageAdapterCreateOptionsDefault()
    {
        // Setup message with null metadata
        ChatMessageContent message = new(AuthorRole.User, "test");

        // Create options
        MessageCreationOptions options = AssistantMessageAdapter.CreateOptions(message);

        // Validate
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
        MessageCreationOptions options = AssistantMessageAdapter.CreateOptions(message);

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
        MessageCreationOptions options = AssistantMessageAdapter.CreateOptions(message);

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
        MessageCreationOptions options = AssistantMessageAdapter.CreateOptions(message);

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
        MessageCreationOptions options = AssistantMessageAdapter.CreateOptions(message);
        MessageContent[] contents = AssistantMessageAdapter.GetMessageContents(message, options).ToArray();
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
        MessageCreationOptions options = AssistantMessageAdapter.CreateOptions(message);
        MessageContent[] contents = AssistantMessageAdapter.GetMessageContents(message, options).ToArray();
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
        MessageCreationOptions options = AssistantMessageAdapter.CreateOptions(message);
        MessageContent[] contents = AssistantMessageAdapter.GetMessageContents(message, options).ToArray();
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
        MessageCreationOptions options = AssistantMessageAdapter.CreateOptions(message);
        MessageContent[] contents = AssistantMessageAdapter.GetMessageContents(message, options).ToArray();
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
        MessageCreationOptions options = AssistantMessageAdapter.CreateOptions(message);
        MessageContent[] contents = AssistantMessageAdapter.GetMessageContents(message, options).ToArray();
        Assert.NotNull(contents);
        Assert.Equal(3, contents.Length);
    }
}
