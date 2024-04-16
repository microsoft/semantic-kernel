// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Azure;
using Xunit;
using Azure.AI.OpenAI;

namespace SemanticKernel.Connectors.Azure.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureChatMessageContentTests"/> class.
/// </summary>
public sealed class AzureChatMessageContentTests
{
    [Fact]
    public void ConstructorsWorkCorrectly()
    {
        // Act
        var content1 = new AzureChatMessageContent(AuthorRole.User, "content2", "model-id1")
        {
            AuthorName = "Fred"
        };
        var content2 = new AzureChatMessageContent(AuthorRole.User, "content2", "model-id2");

        // Assert
        this.AssertChatMessageContent(AuthorRole.User, "content1", "model-id1", content1, "Fred");
        this.AssertChatMessageContent(AuthorRole.User, "content2", "model-id2", content2);
    }

    [Fact]
    public void MetadataIsInitializedCorrectly()
    {
        // Arrange
        var metadata = new Dictionary<string, object?> { { "key", "value" } };

        // Act
        var content1 = new AzureChatMessageContent(AuthorRole.User, "content1", "model-id1", metadata);

        // Assert
        Assert.NotNull(content1.Metadata);
        Assert.Single(content1.Metadata);

        Assert.Equal("value", content1.Metadata["key"]);
    }

    private void AssertChatMessageContent(
        AuthorRole expectedRole,
        string expectedContent,
        string expectedModelId,
        AzureChatMessageContent actualContent,
        string? expectedName = null)
    {
        Assert.Equal(expectedRole, actualContent.Role);
        Assert.Equal(expectedContent, actualContent.Content);
        Assert.Equal(expectedName, actualContent.AuthorName);
        Assert.Equal(expectedModelId, actualContent.ModelId);
    }

    private sealed class FakeChatCompletionsToolCall(string id) : ChatCompletionsToolCall(id)
    { }
}
