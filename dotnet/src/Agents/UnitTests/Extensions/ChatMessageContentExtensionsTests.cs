// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Extensions;

public class ChatMessageContentExtensionsTests
{
    [Fact]
    public void VerifyChatMessageContentExtensionsExistenceTest()
    {
        ChatMessageContent messageWithNullContent = new(AuthorRole.User, content: null);
        ChatMessageContent messageWithEmptyContent = new(AuthorRole.User, content: string.Empty);
        ChatMessageContent messageWithContent = new(AuthorRole.User, content: "hi");
        ChatMessageContent? nullMessage = null;

        Assert.False(nullMessage.HasContent());
        Assert.False(messageWithNullContent.HasContent());
        Assert.False(messageWithEmptyContent.HasContent());
        Assert.True(messageWithContent.HasContent());

        string? content;
        Assert.False(messageWithNullContent.TryGetContent(out content));
        Assert.False(messageWithEmptyContent.TryGetContent(out content));
        Assert.True(messageWithContent.TryGetContent(out content));
        Assert.Equal("hi", content);
    }
}
