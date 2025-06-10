// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
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
        var sut = new ChatMessageContent(AuthorRole.User, content: null)
        {
            Content = "fake-content"
        };

        // Assert
        Assert.Single(sut.Items);

        Assert.Contains(sut.Items, item => item is TextContent textContent && textContent.Text == "fake-content");
    }

    [Theory]
    [InlineData(null)]
    [InlineData("fake-content-1-update")]
    public void ContentPropertySetterShouldUpdateContentOfFirstTextContentItem(string? content)
    {
        // Arrange
        var items = new ChatMessageContentItemCollection
        {
            new ImageContent(new Uri("https://fake-random-test-host:123")),
            new TextContent("fake-content-1"),
            new TextContent("fake-content-2")
        };

        var sut = new ChatMessageContent(AuthorRole.User, items: items)
        {
            Content = content
        };

        Assert.Equal(content, ((TextContent)sut.Items[1]).Text);
    }

    [Fact]
    public void ContentPropertySetterShouldNotAddTextContentToItemsCollection()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: null)
        {
            Content = null
        };

        // Assert
        Assert.Empty(sut.Items);
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
        var items = new ChatMessageContentItemCollection
        {
            new ImageContent(new Uri("https://fake-random-test-host:123")),
            new TextContent("fake-content-1"),
            new TextContent("fake-content-2")
        };

        var sut = new ChatMessageContent(AuthorRole.User, items: items);

        // Act and assert
        Assert.Equal("fake-content-1", sut.Content);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData("\t")]
    [InlineData("\n")]
    [InlineData("\r\n")]
    public void ContentPropertySetterShouldConvertEmptyOrWhitespaceAuthorNameToNull(string? authorName)
    {
        // Arrange
        var message = new ChatMessageContent(AuthorRole.User, content: null)
        {
            AuthorName = authorName
        };

        // Assert
        Assert.Null(message.AuthorName);
    }

    [Fact]
    public void ItShouldBePossibleToSetAndGetEncodingEvenIfThereAreNoItems()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: null)
        {
            Encoding = Encoding.UTF32
        };

        // Assert
        Assert.Empty(sut.Items);
        Assert.Equal(Encoding.UTF32, sut.Encoding);
    }

    [Fact]
    public void EncodingPropertySetterShouldUpdateEncodingTextContentItem()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: "fake-content")
        {
            Encoding = Encoding.UTF32
        };

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
        ChatMessageContentItemCollection items = [
            new TextContent("content-1", "model-1", metadata: new Dictionary<string, object?>() { ["metadata-key-1"] = "metadata-value-1" }) { MimeType = "mime-type-1" },
            new ImageContent(new Uri("https://fake-random-test-host:123")) { ModelId = "model-2", MimeType = "mime-type-2", Metadata = new Dictionary<string, object?>() { ["metadata-key-2"] = "metadata-value-2" } },
            new BinaryContent(new BinaryData(new[] { 1, 2, 3 }), mimeType: "mime-type-3") { ModelId = "model-3", Metadata = new Dictionary<string, object?>() { ["metadata-key-3"] = "metadata-value-3" } },
            new AudioContent(new BinaryData(new[] { 3, 2, 1 }), mimeType: "mime-type-4") { ModelId = "model-4", Metadata = new Dictionary<string, object?>() { ["metadata-key-4"] = "metadata-value-4" } },
            new ImageContent(new BinaryData(new[] { 2, 1, 3 }), mimeType: "mime-type-5") { ModelId = "model-5", Metadata = new Dictionary<string, object?>() { ["metadata-key-5"] = "metadata-value-5" } },
            new TextContent("content-6", "model-6", metadata: new Dictionary<string, object?>() { ["metadata-key-6"] = "metadata-value-6" }) { MimeType = "mime-type-6" },
            new FunctionCallContent("function-name", "plugin-name", "function-id", new KernelArguments { ["parameter"] = "argument" }),
            new FunctionResultContent(new FunctionCallContent("function-name", "plugin-name", "function-id"), "function-result"),
            new FileReferenceContent(fileId: "file-id-1") { ModelId = "model-7", Metadata = new Dictionary<string, object?>() { ["metadata-key-7"] = "metadata-value-7" } },
            new FileReferenceContent(fileId: "file-id-2") { Tools = ["a", "b", "c"] },
            new AnnotationContent(AnnotationKind.TextCitation, "quote-8", "file-id-3") { ModelId = "model-8", StartIndex = 2, EndIndex = 24, Metadata = new Dictionary<string, object?>() { ["metadata-key-8"] = "metadata-value-8" } },
            new ReasoningContent("thinking"),
            new ActionContent("Yes"),
        ];

        // Act
        var chatMessageJson = JsonSerializer.Serialize(new ChatMessageContent(AuthorRole.User, items: items, "message-model", metadata: new Dictionary<string, object?>()
        {
            ["message-metadata-key-1"] = "message-metadata-value-1"
        })
        {
            Content = "content-1-override", // Override the content of the first text content item that has the "content-1" content  
            Source = "Won't make it",
            AuthorName = "Fred"
        });

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
        Assert.True(binaryContent.Data!.Value.Span.SequenceEqual(new BinaryData(new[] { 1, 2, 3 })));
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
        Assert.Equal("function-name", functionResultContent.FunctionName);
        Assert.Equal("function-id", functionResultContent.CallId);
        Assert.Equal("plugin-name", functionResultContent.PluginName);

        var fileReferenceContent1 = deserializedMessage.Items[8] as FileReferenceContent;
        Assert.NotNull(fileReferenceContent1);
        Assert.Equal("file-id-1", fileReferenceContent1.FileId);
        Assert.Equal("model-7", fileReferenceContent1.ModelId);
        Assert.NotNull(fileReferenceContent1.Metadata);
        Assert.Single(fileReferenceContent1.Metadata);
        Assert.Equal("metadata-value-7", fileReferenceContent1.Metadata["metadata-key-7"]?.ToString());

        var fileReferenceContent2 = deserializedMessage.Items[9] as FileReferenceContent;
        Assert.NotNull(fileReferenceContent2);
        Assert.Equal("file-id-2", fileReferenceContent2.FileId);
        Assert.NotNull(fileReferenceContent2.Tools);
        Assert.Equal(3, fileReferenceContent2.Tools.Count);

        var annotationContent = deserializedMessage.Items[10] as AnnotationContent;
        Assert.NotNull(annotationContent);
        Assert.Equal("file-id-3", annotationContent.ReferenceId);
        Assert.Equal("quote-8", annotationContent.Label);
        Assert.Equal(AnnotationKind.TextCitation, annotationContent.Kind);
        Assert.Equal("quote-8", annotationContent.Label);
        Assert.Equal("model-8", annotationContent.ModelId);
        Assert.Equal(2, annotationContent.StartIndex);
        Assert.Equal(24, annotationContent.EndIndex);
        Assert.NotNull(annotationContent.Metadata);
        Assert.Single(annotationContent.Metadata);
        Assert.Equal("metadata-value-8", annotationContent.Metadata["metadata-key-8"]?.ToString());

        var reasoningContent = deserializedMessage.Items[11] as ReasoningContent;
        Assert.NotNull(reasoningContent);
        Assert.Equal("thinking", reasoningContent.Text);

        var actionContent = deserializedMessage.Items[12] as ActionContent;
        Assert.NotNull(actionContent);
        Assert.Equal("Yes", actionContent.Text);
    }

    [Fact]
    public void ItCanBePolymorphicallySerializedAndDeserializedAsKernelContentType()
    {
        // Arrange
        KernelContent sut = new ChatMessageContent(AuthorRole.User, "test-content", "test-model", metadata: new Dictionary<string, object?>()
        {
            ["test-metadata-key"] = "test-metadata-value"
        })
        {
            MimeType = "test-mime-type"
        };

        // Act
        var json = JsonSerializer.Serialize(sut);

        var deserialized = JsonSerializer.Deserialize<KernelContent>(json)!;

        // Assert
        Assert.IsType<ChatMessageContent>(deserialized);
        Assert.Equal("test-content", ((ChatMessageContent)deserialized).Content);
        Assert.Equal("test-model", deserialized.ModelId);
        Assert.Equal("test-mime-type", deserialized.MimeType);
        Assert.NotNull(deserialized.Metadata);
        Assert.Single(deserialized.Metadata);
        Assert.Equal("test-metadata-value", deserialized.Metadata["test-metadata-key"]?.ToString());
    }

    [Fact]
    public void UnknownDerivativeCanBePolymorphicallySerializedAndDeserializedAsChatMessageContentType()
    {
        // Arrange
        KernelContent sut = new UnknownExternalChatMessageContent(AuthorRole.User, "test-content")
        {
            MimeType = "test-mime-type",
        };

        // Act
        var json = JsonSerializer.Serialize(sut);

        var deserialized = JsonSerializer.Deserialize<KernelContent>(json)!;

        // Assert
        Assert.IsType<ChatMessageContent>(deserialized);
        Assert.Equal("test-content", ((ChatMessageContent)deserialized).Content);
        Assert.Equal("test-mime-type", deserialized.MimeType);
    }

    [Fact]
    public void ItCanBeSerializeAndDeserializedWithFunctionResultOfChatMessageType()
    {
        // Arrange
        ChatMessageContentItemCollection items = [
            new FunctionResultContent(new FunctionCallContent("function-name-1", "plugin-name-1", "function-id-1"), new ChatMessageContent(AuthorRole.User, "test-content-1")),
            new FunctionResultContent(new FunctionCallContent("function-name-2", "plugin-name-2", "function-id-2"), new UnknownExternalChatMessageContent(AuthorRole.Assistant, "test-content-2")),
        ];

        // Act
        var chatMessageJson = JsonSerializer.Serialize(new ChatMessageContent(AuthorRole.User, items: items, "message-model"));

        var deserializedMessage = JsonSerializer.Deserialize<ChatMessageContent>(chatMessageJson)!;

        // Assert
        var functionResultContentWithResultOfChatMessageContentType = deserializedMessage.Items[0] as FunctionResultContent;
        Assert.NotNull(functionResultContentWithResultOfChatMessageContentType);
        Assert.Equal("function-name-1", functionResultContentWithResultOfChatMessageContentType.FunctionName);
        Assert.Equal("function-id-1", functionResultContentWithResultOfChatMessageContentType.CallId);
        Assert.Equal("plugin-name-1", functionResultContentWithResultOfChatMessageContentType.PluginName);
        var chatMessageContent = Assert.IsType<JsonElement>(functionResultContentWithResultOfChatMessageContentType.Result);
        Assert.Equal("user", chatMessageContent.GetProperty("Role").GetProperty("Label").GetString());
        Assert.Equal("test-content-1", chatMessageContent.GetProperty("Items")[0].GetProperty("Text").GetString());

        var functionResultContentWithResultOfUnknownChatMessageContentType = deserializedMessage.Items[1] as FunctionResultContent;
        Assert.NotNull(functionResultContentWithResultOfUnknownChatMessageContentType);
        Assert.Equal("function-name-2", functionResultContentWithResultOfUnknownChatMessageContentType.FunctionName);
        Assert.Equal("function-id-2", functionResultContentWithResultOfUnknownChatMessageContentType.CallId);
        Assert.Equal("plugin-name-2", functionResultContentWithResultOfUnknownChatMessageContentType.PluginName);
        var unknownChatMessageContent = Assert.IsType<JsonElement>(functionResultContentWithResultOfUnknownChatMessageContentType.Result);
        Assert.Equal("assistant", unknownChatMessageContent.GetProperty("Role").GetProperty("Label").GetString());
        Assert.Equal("test-content-2", unknownChatMessageContent.GetProperty("Items")[0].GetProperty("Text").GetString());
    }

    private sealed class UnknownExternalChatMessageContent : ChatMessageContent
    {
        public UnknownExternalChatMessageContent(AuthorRole role, string? content) : base(role, content)
        {
        }
    }
}
