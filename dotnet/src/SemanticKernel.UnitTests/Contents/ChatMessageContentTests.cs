// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

// This tests a type that contains experimental features.
#pragma warning disable SKEXP0001
#pragma warning disable SKEXP0010
#pragma warning disable SKEXP0101

namespace SemanticKernel.UnitTests.Contents;
public class ChatMessageContentTests
{
    [Fact]
    public void ConstructorShouldAddTextContentToItemsCollectionIfContentProvided()
    {
        // Arrange & act
        var sut = new ChatMessageContent(AuthorRole.User, "fake-content");

        // Assert
        Assert.Single(sut.Items);

        Assert.Contains(sut.Items, item => item is TextContent textContent && textContent.Text == "fake-content");
    }

    [Fact]
    public void ConstructorShouldNodAddTextContentToItemsCollectionIfNoContentProvided()
    {
        // Arrange & act
        var sut = new ChatMessageContent(AuthorRole.User, content: null);

        // Assert
        Assert.Empty(sut.Items);
    }

    [Fact]
    public void ContentPropertySetterShouldAddTextContentToItemsCollection()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: null);

        // Act
        sut.Content = "fake-content";

        // Assert
        Assert.Single(sut.Items);

        Assert.Contains(sut.Items, item => item is TextContent textContent && textContent.Text == "fake-content");
    }

    [Fact]
    public void ContentPropertySetterShouldUpdateContentOfFirstTextContentItem()
    {
        // Arrange
        var items = new ChatMessageContentItemCollection();
        items.Add(new ImageContent(new Uri("https://fake-random-test-host:123")));
        items.Add(new TextContent("fake-content-1"));
        items.Add(new TextContent("fake-content-2"));

        var sut = new ChatMessageContent(AuthorRole.User, items: items);

        // Act
        sut.Content = "fake-content-1-update";

        Assert.Equal("fake-content-1-update", ((TextContent)sut.Items[1]).Text);
    }

    [Fact]
    public void ContentPropertyGetterShouldReturnNullIfThereAreNoTextContentItems()
    {
        // Arrange and act
        var sut = new ChatMessageContent(AuthorRole.User, content: null);

        // Assert
        Assert.Null(sut.Content);
        Assert.Equal(string.Empty, sut.ToString());
    }

    [Fact]
    public void ContentPropertyGetterShouldReturnContentOfTextContentItem()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, "fake-content");

        // Act and assert
        Assert.Equal("fake-content", sut.Content);
        Assert.Equal("fake-content", sut.ToString());
    }

    [Fact]
    public void ContentPropertyGetterShouldReturnContentOfTheFirstTextContentItem()
    {
        // Arrange
        var items = new ChatMessageContentItemCollection();
        items.Add(new ImageContent(new Uri("https://fake-random-test-host:123")));
        items.Add(new TextContent("fake-content-1"));
        items.Add(new TextContent("fake-content-2"));

        var sut = new ChatMessageContent(AuthorRole.User, items: items);

        // Act and assert
        Assert.Equal("fake-content-1", sut.Content);
    }

    [Fact]
    public void ItShouldBePossibleToSetAndGetEncodingEvenIfThereAreNoItems()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: null);

        // Act
        sut.Encoding = Encoding.UTF32;

        // Assert
        Assert.Empty(sut.Items);
        Assert.Equal(Encoding.UTF32, sut.Encoding);
    }

    [Fact]
    public void EncodingPropertySetterShouldUpdateEncodingTextContentItem()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: "fake-content");

        // Act
        sut.Encoding = Encoding.UTF32;

        // Assert
        Assert.Single(sut.Items);
        Assert.Equal(Encoding.UTF32, ((TextContent)sut.Items[0]).Encoding);
    }

    [Fact]
    public void EncodingPropertyGetterShouldReturnEncodingOfTextContentItem()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: "fake-content");

        // Act
        ((TextContent)sut.Items[0]).Encoding = Encoding.Latin1;

        // Assert
        Assert.Equal(Encoding.Latin1, sut.Encoding);
    }

    [Fact]
    public void ItCanBeSerializeAndDeserialized()
    {
        // Arrange
        var items = new ChatMessageContentItemCollection();
        items.Add(new TextContent("content-1", "model-1", metadata: new Dictionary<string, object?>()
        {
            ["metadata-key-1"] = "metadata-value-1"
        })
        { MimeType = "mime-type-1" });

        items.Add(new ImageContent(new Uri("https://fake-random-test-host:123"), "model-2", metadata: new Dictionary<string, object?>()
        {
            ["metadata-key-2"] = "metadata-value-2"
        })
        { MimeType = "mime-type-2" });

#pragma warning disable SKEXP0010
        items.Add(new BinaryContent(new BinaryData(new[] { 1, 2, 3 }), "model-3", metadata: new Dictionary<string, object?>()
        {
            ["metadata-key-3"] = "metadata-value-3"
        })
        { MimeType = "mime-type-3" });

#pragma warning restore SKEXP0010
#pragma warning disable SKEXP0001
        items.Add(new AudioContent(new BinaryData(new[] { 3, 2, 1 }), "model-4", metadata: new Dictionary<string, object?>()
        {
            ["metadata-key-4"] = "metadata-value-4"
        })
        { MimeType = "mime-type-4" });

#pragma warning restore SKEXP0001
        items.Add(new ImageContent(new BinaryData(new[] { 2, 1, 3 }), "model-5", metadata: new Dictionary<string, object?>()
        {
            ["metadata-key-5"] = "metadata-value-5"
        })
        { MimeType = "mime-type-5" });

        items.Add(new TextContent("content-6", "model-6", metadata: new Dictionary<string, object?>()
        {
            ["metadata-key-6"] = "metadata-value-6"
        })
        { MimeType = "mime-type-6" });

        items.Add(new FunctionCallContent("function-name", "plugin-name", "function-id", new KernelArguments { ["parameter"] = "argument" }));

        items.Add(new FunctionResultContent(new FunctionCallContent("function-name", "plugin-name", "function-id"), "function-result"));

        var sut = new ChatMessageContent(AuthorRole.User, items: items, "message-model", metadata: new Dictionary<string, object?>()
        {
            ["message-metadata-key-1"] = "message-metadata-value-1"
        });
        sut.Content = "content-1-override"; // Override the content of the first text content item that has the "content-1" content  
        sut.Source = "Won't make it";
        sut.AuthorName = "Fred";

        // Act
        var chatMessageJson = JsonSerializer.Serialize(sut);

        var deserializedMessage = JsonSerializer.Deserialize<ChatMessageContent>(chatMessageJson)!;

        // Assert
        Assert.Equal("message-model", deserializedMessage.ModelId);
        Assert.Equal("Fred", deserializedMessage.AuthorName);
        Assert.Equal("message-model", deserializedMessage.ModelId);
        Assert.Equal("user", deserializedMessage.Role.Label);
        Assert.NotNull(deserializedMessage.Metadata);
        Assert.Single(deserializedMessage.Metadata);
        Assert.Equal("message-metadata-value-1", deserializedMessage.Metadata["message-metadata-key-1"]?.ToString());
        Assert.Null(deserializedMessage.Source);

        Assert.NotNull(deserializedMessage?.Items);
        Assert.Equal(items.Count, deserializedMessage.Items.Count);

        var textContent = deserializedMessage.Items[0] as TextContent;
        Assert.NotNull(textContent);
        Assert.Equal("content-1-override", textContent.Text);
        Assert.Equal("model-1", textContent.ModelId);
        Assert.Equal("mime-type-1", textContent.MimeType);
        Assert.NotNull(textContent.Metadata);
        Assert.Single(textContent.Metadata);
        Assert.Equal("metadata-value-1", textContent.Metadata["metadata-key-1"]?.ToString());

        var imageContent = deserializedMessage.Items[1] as ImageContent;
        Assert.NotNull(imageContent);
        Assert.Equal("https://fake-random-test-host:123", imageContent.Uri?.OriginalString);
        Assert.Equal("model-2", imageContent.ModelId);
        Assert.Equal("mime-type-2", imageContent.MimeType);
        Assert.NotNull(imageContent.Metadata);
        Assert.Single(imageContent.Metadata);
        Assert.Equal("metadata-value-2", imageContent.Metadata["metadata-key-2"]?.ToString());

        var binaryContent = deserializedMessage.Items[2] as BinaryContent;
        Assert.NotNull(binaryContent);
        Assert.True(binaryContent.Content?.Span.SequenceEqual(new BinaryData(new[] { 1, 2, 3 })));
        Assert.Equal("model-3", binaryContent.ModelId);
        Assert.Equal("mime-type-3", binaryContent.MimeType);
        Assert.NotNull(binaryContent.Metadata);
        Assert.Single(binaryContent.Metadata);
        Assert.Equal("metadata-value-3", binaryContent.Metadata["metadata-key-3"]?.ToString());

        var audioContent = deserializedMessage.Items[3] as AudioContent;
        Assert.NotNull(audioContent);
        Assert.True(audioContent.Data!.Value.Span.SequenceEqual(new BinaryData(new[] { 3, 2, 1 })));
        Assert.Equal("model-4", audioContent.ModelId);
        Assert.Equal("mime-type-4", audioContent.MimeType);
        Assert.NotNull(audioContent.Metadata);
        Assert.Single(audioContent.Metadata);
        Assert.Equal("metadata-value-4", audioContent.Metadata["metadata-key-4"]?.ToString());

        imageContent = deserializedMessage.Items[4] as ImageContent;
        Assert.NotNull(imageContent);
        Assert.True(imageContent.Data?.Span.SequenceEqual(new BinaryData(new[] { 2, 1, 3 })));
        Assert.Equal("model-5", imageContent.ModelId);
        Assert.Equal("mime-type-5", imageContent.MimeType);
        Assert.NotNull(imageContent.Metadata);
        Assert.Single(imageContent.Metadata);
        Assert.Equal("metadata-value-5", imageContent.Metadata["metadata-key-5"]?.ToString());

        textContent = deserializedMessage.Items[5] as TextContent;
        Assert.NotNull(textContent);
        Assert.Equal("content-6", textContent.Text);
        Assert.Equal("model-6", textContent.ModelId);
        Assert.Equal("mime-type-6", textContent.MimeType);
        Assert.NotNull(textContent.Metadata);
        Assert.Single(textContent.Metadata);
        Assert.Equal("metadata-value-6", textContent.Metadata["metadata-key-6"]?.ToString());

        var functionCallContent = deserializedMessage.Items[6] as FunctionCallContent;
        Assert.NotNull(functionCallContent);
        Assert.Equal("function-name", functionCallContent.FunctionName);
        Assert.Equal("plugin-name", functionCallContent.PluginName);
        Assert.Equal("function-id", functionCallContent.Id);
        Assert.NotNull(functionCallContent.Arguments);
        Assert.Single(functionCallContent.Arguments);
        Assert.Equal("argument", functionCallContent.Arguments["parameter"]?.ToString());

        var functionResultContent = deserializedMessage.Items[7] as FunctionResultContent;
        Assert.NotNull(functionResultContent);
        Assert.Equal("function-result", functionResultContent.Result?.ToString());
        Assert.Equal("function-name", functionResultContent.FunctionCall.FunctionName);
        Assert.Equal("function-id", functionResultContent.FunctionCall.Id);
        Assert.Equal("plugin-name", functionResultContent.FunctionCall.PluginName);
    }

    [Fact]
    public void GetFunctionCallsShouldReturnItemsOfFunctionCallContentType()
    {
        // Arrange
        var items = new ChatMessageContentItemCollection();
        items.Add(new TextContent("content-1"));
        items.Add(new FunctionCallContent("function-name", "plugin-name", "function-id", new KernelArguments { ["parameter"] = "argument" }));
        items.Add(new FunctionCallContent("function-name-1", "plugin-name-1", "function-id-1", new KernelArguments { ["parameter-1"] = "argument-1" }));
        items.Add(new FunctionResultContent(new FunctionCallContent("function-name", "plugin-name", "function-id"), "function-result"));

        var sut = new ChatMessageContent(AuthorRole.Tool, items);

        // Act
        var functionCallContents = sut.GetFunctionCalls().ToArray();

        // Assert
        Assert.NotNull(functionCallContents);
        Assert.Equal(2, functionCallContents.Length);

        Assert.True(functionCallContents.All(item => item is FunctionCallContent));
    }
}
