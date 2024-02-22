// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;
public class ChatMessageContentTests
{
    [Fact]
    public void ItCanBeSerializeAndDeserialized()
    {
        // Arrange
        var items = new ChatMessageContentItemCollection();
        items.Add(new TextContent("content-1", "model-1", metadata: new Dictionary<string, object?>()
        {
            ["metadata-key-1"] = "metadata-value-1"
        }));
        items.Add(new ImageContent(new Uri("https://fake-random-test-host:123"), "model-2", metadata: new Dictionary<string, object?>()
        {
            ["metadata-key-2"] = "metadata-value-2"
        }));
        items.Add(new BinaryContent(new BinaryData(new[] { 1, 2, 3 }), "model-3", metadata: new Dictionary<string, object?>()
        {
            ["metadata-key-3"] = "metadata-value-3"
        }));
#pragma warning disable SKEXP0005
        items.Add(new AudioContent(new BinaryData(new[] { 3, 2, 1 }), "model-4", metadata: new Dictionary<string, object?>()
        {
            ["metadata-key-4"] = "metadata-value-4"
        }));
#pragma warning disable SKEXP0005

        var sut = new ChatMessageContent(AuthorRole.User, items: items, "message-model", metadata: new Dictionary<string, object?>()
        {
            ["message-metadata-key-1"] = "message-metadata-value-1"
        });
        sut.Content = "message-content";

        // Act
        var chatMessageJson = JsonSerializer.Serialize(sut);

        var deserializedMessage = JsonSerializer.Deserialize<ChatMessageContent>(chatMessageJson);

        // Assert
        Assert.Equal("message-content", sut.Content);
        Assert.Equal("message-model", sut.ModelId);
        Assert.Equal("user", sut.Role.Label);
        Assert.NotNull(sut.Metadata);
        Assert.Single(sut.Metadata);
        Assert.Equal("message-metadata-value-1", sut.Metadata["message-metadata-key-1"]?.ToString());

        Assert.NotNull(deserializedMessage?.Items);
        Assert.Equal(4, deserializedMessage.Items.Count);

        var textContent = deserializedMessage.Items[0] as TextContent;
        Assert.NotNull(textContent);
        Assert.Equal("content-1", textContent.Text);
        Assert.Equal("model-1", textContent.ModelId);
        Assert.NotNull(textContent.Metadata);
        Assert.Single(textContent.Metadata);
        Assert.Equal("metadata-value-1", textContent.Metadata["metadata-key-1"]?.ToString());

        var imageContent = deserializedMessage.Items[1] as ImageContent;
        Assert.NotNull(imageContent);
        Assert.Equal("https://fake-random-test-host:123", imageContent.Uri?.OriginalString);
        Assert.Equal("model-2", imageContent.ModelId);
        Assert.NotNull(imageContent.Metadata);
        Assert.Single(imageContent.Metadata);
        Assert.Equal("metadata-value-2", imageContent.Metadata["metadata-key-2"]?.ToString());

        var binaryContent = deserializedMessage.Items[2] as BinaryContent;
        Assert.NotNull(binaryContent);
        Assert.True(binaryContent.Content?.ToArray().SequenceEqual(new BinaryData(new[] { 1, 2, 3 }).ToArray()));
        Assert.Equal("model-3", binaryContent.ModelId);
        Assert.NotNull(binaryContent.Metadata);
        Assert.Single(binaryContent.Metadata);
        Assert.Equal("metadata-value-3", binaryContent.Metadata["metadata-key-3"]?.ToString());

        var audioContent = deserializedMessage.Items[3] as AudioContent;
        Assert.NotNull(audioContent);
        Assert.True(audioContent.Data?.ToArray().SequenceEqual(new BinaryData(new[] { 3, 2, 1 }).ToArray()));
        Assert.Equal("model-4", audioContent.ModelId);
        Assert.NotNull(audioContent.Metadata);
        Assert.Single(audioContent.Metadata);
        Assert.Equal("metadata-value-4", audioContent.Metadata["metadata-key-4"]?.ToString());
    }
}
