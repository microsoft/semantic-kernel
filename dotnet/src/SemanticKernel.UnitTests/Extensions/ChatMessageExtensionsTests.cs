// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="ChatMessageExtensions"/> class.
/// </summary>
public sealed class ChatMessageExtensionsTests
{
    [Fact]
    public void ToChatMessageContentWithTextContentReturnsCorrectChatMessageContent()
    {
        // Arrange
        var chatMessage = new ChatMessage(ChatRole.User, "Hello, world!");

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(AuthorRole.User, result.Role);
        Assert.Single(result.Items);
        var textContent = Assert.IsType<Microsoft.SemanticKernel.TextContent>(result.Items[0]);
        Assert.Equal("Hello, world!", textContent.Text);
    }

    [Fact]
    public void ToChatMessageContentWithAuthorNameSetsAuthorName()
    {
        // Arrange
        var chatMessage = new ChatMessage(ChatRole.Assistant, "Response")
        {
            AuthorName = "TestAssistant"
        };

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Equal("TestAssistant", result.AuthorName);
    }

    [Fact]
    public void ToChatMessageContentWithResponseSetsModelIdFromResponse()
    {
        // Arrange
        var chatMessage = new ChatMessage(ChatRole.Assistant, "Response");
        var response = new ChatResponse(new[] { chatMessage })
        {
            ModelId = "gpt-4"
        };

        // Act
        var result = chatMessage.ToChatMessageContent(response);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("gpt-4", result.ModelId);
    }

    [Fact]
    public void ToChatMessageContentWithImageDataContentCreatesImageContent()
    {
        // Arrange
        var imageUri = new Uri("data:image/png;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA");
        var chatMessage = new ChatMessage(ChatRole.User, [
            new DataContent(imageUri, "image/png")
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var imageContent = Assert.IsType<Microsoft.SemanticKernel.ImageContent>(result.Items[0]);
        Assert.Equal(imageUri.OriginalString, imageContent.DataUri);
    }

    [Fact]
    public void ToChatMessageContentWithImageUriContentCreatesImageContent()
    {
        // Arrange
        var imageUri = new Uri("https://example.com/image.jpg");
        var chatMessage = new ChatMessage(ChatRole.User, [
            new UriContent(imageUri, "image/jpeg")
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var imageContent = Assert.IsType<Microsoft.SemanticKernel.ImageContent>(result.Items[0]);
        Assert.Equal(imageUri, imageContent.Uri);
    }

    [Fact]
    public void ToChatMessageContentWithAudioDataContentCreatesAudioContent()
    {
        // Arrange
        var audioUri = new Uri("data:audio/mpeg;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA");
        var chatMessage = new ChatMessage(ChatRole.User, [
            new DataContent(audioUri, "audio/mpeg")
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var audioContent = Assert.IsType<Microsoft.SemanticKernel.AudioContent>(result.Items[0]);
        Assert.Equal(audioUri.OriginalString, audioContent.DataUri);
    }

    [Fact]
    public void ToChatMessageContentWithAudioUriContentCreatesAudioContent()
    {
        // Arrange
        var audioUri = new Uri("http://example.com/audio.wav");
        var chatMessage = new ChatMessage(ChatRole.User, [
            new UriContent(audioUri, "audio/wav")
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var audioContent = Assert.IsType<Microsoft.SemanticKernel.AudioContent>(result.Items[0]);
        Assert.Equal(audioUri, audioContent.Uri);
    }

    [Fact]
    public void ToChatMessageContentWithBinaryDataContentCreatesBinaryContent()
    {
        // Arrange
        var dataUri = new Uri("data:application/octet-stream;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQAAAAA=");
        var chatMessage = new ChatMessage(ChatRole.User, [
            new DataContent(dataUri, "application/octet-stream")
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var binaryContent = Assert.IsType<Microsoft.SemanticKernel.BinaryContent>(result.Items[0]);
        Assert.Equal(dataUri.OriginalString, binaryContent.DataUri);
    }

    [Fact]
    public void ToChatMessageContentWithBinaryUriContentCreatesBinaryContent()
    {
        // Arrange
        var dataUri = new Uri("https://example.com/data.pdf");
        var chatMessage = new ChatMessage(ChatRole.User, [
            new UriContent(dataUri, "application/pdf")
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var binaryContent = Assert.IsType<Microsoft.SemanticKernel.BinaryContent>(result.Items[0]);
        Assert.Equal(dataUri, binaryContent.Uri);
    }

    [Fact]
    public void ToChatMessageContentWithFunctionCallContentCreatesFunctionCallContent()
    {
        // Arrange
        var arguments = new Dictionary<string, object?> { { "param1", "value1" } };
        var chatMessage = new ChatMessage(ChatRole.Assistant, [
            new Microsoft.Extensions.AI.FunctionCallContent("call-123", "MyFunction", arguments)
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var functionCall = Assert.IsType<Microsoft.SemanticKernel.FunctionCallContent>(result.Items[0]);
        Assert.Equal("call-123", functionCall.Id);
        Assert.Equal("MyFunction", functionCall.FunctionName);
        Assert.NotNull(functionCall.Arguments);
    }

    [Fact]
    public void ToChatMessageContentWithUnderscoreQualifiedFunctionCallParsesPluginAndFunction()
    {
        // Arrange
        var chatMessage = new ChatMessage(ChatRole.Assistant, [
            new Microsoft.Extensions.AI.FunctionCallContent("call-123", "time_ReadFile")
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var functionCall = Assert.IsType<Microsoft.SemanticKernel.FunctionCallContent>(result.Items[0]);
        Assert.Equal("time", functionCall.PluginName);
        Assert.Equal("ReadFile", functionCall.FunctionName);
    }

    [Fact]
    public void ToChatMessageContentWithSnakeCaseFunctionNameDoesNotSplitIntoPluginAndFunction()
    {
        // Arrange
        var chatMessage = new ChatMessage(ChatRole.Assistant, [
            new Microsoft.Extensions.AI.FunctionCallContent("call-123", "my_function")
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var functionCall = Assert.IsType<Microsoft.SemanticKernel.FunctionCallContent>(result.Items[0]);
        Assert.Null(functionCall.PluginName);
        Assert.Equal("my_function", functionCall.FunctionName);
    }

    [Fact]
    public void ToChatMessageContentWithFunctionResultContentCreatesFunctionResultContent()
    {
        // Arrange
        var functionCallMessage = new ChatMessage(ChatRole.Assistant, [
            new Microsoft.Extensions.AI.FunctionCallContent("call-123", "MyFunction")
        ]);
        var resultMessage = new ChatMessage(ChatRole.Tool, [
            new Microsoft.Extensions.AI.FunctionResultContent("call-123", "result value")
        ]);
        var response = new ChatResponse(new[] { functionCallMessage, resultMessage });

        // Act
        var result = resultMessage.ToChatMessageContent(response);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var functionResult = Assert.IsType<Microsoft.SemanticKernel.FunctionResultContent>(result.Items[0]);
        Assert.Equal("call-123", functionResult.CallId);
        Assert.Equal("MyFunction", functionResult.FunctionName);
        Assert.Equal("result value", functionResult.Result);
    }

    [Fact]
    public void ToChatMessageContentWithFunctionResultContentParsesPluginNameFromMatchedFunctionCall()
    {
        // Arrange
        var functionCallMessage = new ChatMessage(ChatRole.Assistant, [
            new Microsoft.Extensions.AI.FunctionCallContent("call-123", "time_ReadFile")
        ]);
        var resultMessage = new ChatMessage(ChatRole.Tool, [
            new Microsoft.Extensions.AI.FunctionResultContent("call-123", "result value")
        ]);
        var response = new ChatResponse(new[] { functionCallMessage, resultMessage });

        // Act
        var result = resultMessage.ToChatMessageContent(response);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var functionResult = Assert.IsType<Microsoft.SemanticKernel.FunctionResultContent>(result.Items[0]);
        Assert.Equal("time", functionResult.PluginName);
        Assert.Equal("ReadFile", functionResult.FunctionName);
        Assert.Equal("result value", functionResult.Result);
    }

    [Fact]
    public void ToChatMessageContentWithMultipleContentItemsCreatesMultipleItems()
    {
        // Arrange
        var chatMessage = new ChatMessage(ChatRole.User, [
            new Microsoft.Extensions.AI.TextContent("Hello"),
            new Microsoft.Extensions.AI.TextContent("World")
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(2, result.Items.Count);
        Assert.All(result.Items, item => Assert.IsType<Microsoft.SemanticKernel.TextContent>(item));
    }

    [Fact]
    public void ToChatMessageContentWithAdditionalPropertiesSetsMetadata()
    {
        // Arrange
        var additionalProps = new AdditionalPropertiesDictionary
        {
            { "customKey", "customValue" }
        };
        var chatMessage = new ChatMessage(ChatRole.User, "Test")
        {
            AdditionalProperties = additionalProps
        };

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Metadata);
        Assert.True(result.Metadata.ContainsKey("customKey"));
        Assert.Equal("customValue", result.Metadata["customKey"]);
    }

    [Fact]
    public void ToChatMessageContentWithUsageInResponseSetsUsageInMetadata()
    {
        // Arrange
        var chatMessage = new ChatMessage(ChatRole.Assistant, "Response");
        var usage = new UsageDetails
        {
            InputTokenCount = 10,
            OutputTokenCount = 20
        };
        var response = new ChatResponse(new[] { chatMessage })
        {
            Usage = usage
        };

        // Act
        var result = chatMessage.ToChatMessageContent(response);

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Metadata);
        Assert.True(result.Metadata.ContainsKey("Usage"));
        Assert.Same(usage, result.Metadata["Usage"]);
    }

    [Fact]
    public void ToChatMessageContentWithRawRepresentationSetsInnerContent()
    {
        // Arrange
        var rawObject = new { test = "value" };
        var chatMessage = new ChatMessage(ChatRole.User, "Test")
        {
            RawRepresentation = rawObject
        };

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Same(rawObject, result.InnerContent);
    }

    [Fact]
    public void ToChatMessageContentWithResponseRawRepresentationUsesResponseRawRepresentation()
    {
        // Arrange
        var messageRaw = new { message = "value" };
        var responseRaw = new { response = "value" };
        var chatMessage = new ChatMessage(ChatRole.User, "Test")
        {
            RawRepresentation = messageRaw
        };
        var response = new ChatResponse(new[] { chatMessage })
        {
            RawRepresentation = responseRaw
        };

        // Act
        var result = chatMessage.ToChatMessageContent(response);

        // Assert
        Assert.NotNull(result);
        Assert.Same(responseRaw, result.InnerContent);
    }

    [Fact]
    public void ToChatMessageContentSetsContentMetadataFromAIContent()
    {
        // Arrange
        var contentProps = new AdditionalPropertiesDictionary { { "contentKey", "contentValue" } };
        var contentRaw = new { content = "raw" };
        var textContent = new Microsoft.Extensions.AI.TextContent("Hello")
        {
            AdditionalProperties = contentProps,
            RawRepresentation = contentRaw
        };
        var chatMessage = new ChatMessage(ChatRole.User, [textContent]);
        var response = new ChatResponse(new[] { chatMessage })
        {
            ModelId = "gpt-4"
        };

        // Act
        var result = chatMessage.ToChatMessageContent(response);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var resultContent = result.Items[0];
        Assert.NotNull(resultContent.Metadata);
        Assert.Equal("contentValue", resultContent.Metadata["contentKey"]);
        Assert.Same(contentRaw, resultContent.InnerContent);
        Assert.Equal("gpt-4", resultContent.ModelId);
    }

    [Fact]
    public void ToChatHistoryWithEmptyCollectionReturnsEmptyChatHistory()
    {
        // Arrange
        var messages = Array.Empty<ChatMessage>();

        // Act
        var result = messages.ToChatHistory();

        // Assert
        Assert.NotNull(result);
        Assert.Empty(result);
    }

    [Fact]
    public void ToChatHistoryWithMultipleMessagesReturnsCorrectChatHistory()
    {
        // Arrange
        var messages = new[]
        {
            new ChatMessage(ChatRole.System, "You are a helpful assistant."),
            new ChatMessage(ChatRole.User, "Hello!"),
            new ChatMessage(ChatRole.Assistant, "Hi there! How can I help you?")
        };

        // Act
        var result = messages.ToChatHistory();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(3, result.Count);
        Assert.Equal(AuthorRole.System, result[0].Role);
        Assert.Equal(AuthorRole.User, result[1].Role);
        Assert.Equal(AuthorRole.Assistant, result[2].Role);
    }

    [Fact]
    public void ToChatHistoryPreservesMessageOrder()
    {
        // Arrange
        var messages = new[]
        {
            new ChatMessage(ChatRole.User, "First"),
            new ChatMessage(ChatRole.Assistant, "Second"),
            new ChatMessage(ChatRole.User, "Third")
        };

        // Act
        var result = messages.ToChatHistory();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(3, result.Count);
        Assert.Equal("First", ((Microsoft.SemanticKernel.TextContent)result[0].Items[0]).Text);
        Assert.Equal("Second", ((Microsoft.SemanticKernel.TextContent)result[1].Items[0]).Text);
        Assert.Equal("Third", ((Microsoft.SemanticKernel.TextContent)result[2].Items[0]).Text);
    }

    [Fact]
    public void ToChatHistoryWithComplexMessagesConvertsAllContent()
    {
        // Arrange
        var imageUri = new Uri("https://example.com/image.png");
        var messages = new[]
        {
            new ChatMessage(ChatRole.User, [
                new Microsoft.Extensions.AI.TextContent("Look at this image:"),
                new UriContent(imageUri, "image/png")
            ])
        };

        // Act
        var result = messages.ToChatHistory();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal(2, result[0].Items.Count);
        Assert.IsType<Microsoft.SemanticKernel.TextContent>(result[0].Items[0]);
        Assert.IsType<Microsoft.SemanticKernel.ImageContent>(result[0].Items[1]);
    }

    [Fact]
    public void ToChatMessageContentWithNullFunctionCallIdDoesNotThrow()
    {
        // Arrange
        var chatMessage = new ChatMessage(ChatRole.Tool, [
            new Microsoft.Extensions.AI.FunctionResultContent("call-456", "result")
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items);
        var functionResult = Assert.IsType<Microsoft.SemanticKernel.FunctionResultContent>(result.Items[0]);
        Assert.Null(functionResult.FunctionName);
    }

    [Fact]
    public void ToChatMessageContentWithSystemRoleMapsToSystemRole()
    {
        // Arrange
        var chatMessage = new ChatMessage(ChatRole.System, "You are helpful.");

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(AuthorRole.System, result.Role);
    }

    [Fact]
    public void ToChatMessageContentWithToolRoleMapsToToolRole()
    {
        // Arrange
        var chatMessage = new ChatMessage(ChatRole.Tool, "Tool result");

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Equal(AuthorRole.Tool, result.Role);
    }

    [Fact]
    public void ToChatMessageContentWithUnknownContentTypeSkipsContent()
    {
        // Arrange
        var chatMessage = new ChatMessage(ChatRole.User, [
            new Microsoft.Extensions.AI.TextContent("Valid text"),
            new CustomAIContent() // Unknown content type
        ]);

        // Act
        var result = chatMessage.ToChatMessageContent();

        // Assert
        Assert.NotNull(result);
        Assert.Single(result.Items); // Only the text content should be included
        Assert.IsType<Microsoft.SemanticKernel.TextContent>(result.Items[0]);
    }

    /// <summary>
    /// Custom AI content type for testing unknown content handling
    /// </summary>
    private sealed class CustomAIContent : AIContent
    {
    }
}
