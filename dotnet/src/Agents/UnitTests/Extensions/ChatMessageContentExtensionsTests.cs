// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Extensions;

/// <summary>
/// Unit testing of <see cref="ChatMessageContentExtensions"/>.
/// </summary>
public class ChatMessageContentExtensionsTests
{
    /// <summary>
    /// Verify behavior of content accessor extensions for <see cref="ChatMessageContent"/>.
    /// </summary>
    [Fact]
    public void VerifyChatMessageContentExtensionsExistence()
    {
        // Create various messages
        ChatMessageContent messageWithNullContent = new(AuthorRole.User, content: null);
        ChatMessageContent messageWithEmptyContent = new(AuthorRole.User, content: string.Empty);
        ChatMessageContent messageWithContent = new(AuthorRole.User, content: "hi");
        ChatMessageContent? nullMessage = null;

        // Verify HasContent
        Assert.False(nullMessage.HasContent());
        Assert.False(messageWithNullContent.HasContent());
        Assert.False(messageWithEmptyContent.HasContent());
        Assert.True(messageWithContent.HasContent());

        // Verify TryGetContent
        Assert.False(messageWithNullContent.TryGetContent(out string? content));
        Assert.False(messageWithEmptyContent.TryGetContent(out content));
        Assert.True(messageWithContent.TryGetContent(out content));
        Assert.Equal("hi", content);
    }
}
