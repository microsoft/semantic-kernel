// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.ClientModel;
using System.ClientModel;
using System.ClientModel;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;

#pragma warning disable CS0618 // AzureOpenAIChatCompletionWithData is deprecated in favor of OpenAIPromptExecutionSettings.AzureChatExtensionsOptions

/// <summary>
/// Unit tests for <see cref="OpenAIStreamingChatMessageContent"/> class.
/// </summary>
public sealed class OpenAIStreamingChatMessageContentTests
{
    [Fact]
    public async Task ConstructorWithStreamingUpdateAsync()
    {
        // Arrange
        using var stream = File.OpenRead("TestData/chat_completion_streaming_test_response.txt");

        using var messageHandlerStub = new HttpMessageHandlerStub();
        messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StreamContent(stream)
        };

        using var httpClient = new HttpClient(messageHandlerStub);
        var openAIClient = new OpenAIClient("key", new() { Transport = new HttpClientPipelineTransport(httpClient) });
        var openAIClient = new OpenAIClient("key", new() { Transport = new HttpClientPipelineTransport(httpClient) });
        var openAIClient = new OpenAIClient(new ApiKeyCredential("key"), new() { Transport = new HttpClientPipelineTransport(httpClient) });
        var openAIClient = new OpenAIClient(new ApiKeyCredential("key"), new() { Transport = new HttpClientPipelineTransport(httpClient) });
        var openAIClient = new OpenAIClient(new ApiKeyCredential("key"), new() { Transport = new HttpClientPipelineTransport(httpClient) });
        var openAIClient = new OpenAIClient(new ApiKeyCredential("key"), new() { Transport = new HttpClientPipelineTransport(httpClient) });

        // Act & Assert
        var enumerator = openAIClient.GetChatClient("modelId").CompleteChatStreamingAsync("Test message").GetAsyncEnumerator();

        await enumerator.MoveNextAsync();
        var update = enumerator.Current;

        // Act
        var content = new OpenAIStreamingChatMessageContent(update!, 0, "model-id");

        // Assert
        Assert.Equal("Test chat streaming response", content.Content);
    }

    [Fact]
    public void ConstructorWithParameters()
    {
        // Act
        var content = new OpenAIStreamingChatMessageContent(
            authorRole: AuthorRole.User,
            content: "test message",
            choiceIndex: 0,
            modelId: "testModel",
            toolCallUpdates: [],
            metadata: new Dictionary<string, object?>() { ["test-index"] = "test-value" });

        // Assert
        Assert.Equal("test message", content.Content);
        Assert.Equal(AuthorRole.User, content.Role);
        Assert.Equal(0, content.ChoiceIndex);
        Assert.Equal("testModel", content.ModelId);
        Assert.Empty(content.ToolCallUpdates!);
        Assert.Equal("test-value", content.Metadata!["test-index"]);
        Assert.Equal(Encoding.UTF8, content.Encoding);
    }

    [Fact]
    public void ToStringReturnsAsExpected()
    {
        // Act
        var content = new OpenAIStreamingChatMessageContent(
            authorRole: AuthorRole.User,
            content: "test message",
            choiceIndex: 0,
            modelId: "testModel",
            toolCallUpdates: [],
            metadata: new Dictionary<string, object?>() { ["test-index"] = "test-value" });

        // Assert
        Assert.Equal("test message", content.ToString());
    }

    [Fact]
    public void ToByteArrayReturnsAsExpected()
    {
        // Act
        var content = new OpenAIStreamingChatMessageContent(
            authorRole: AuthorRole.User,
            content: "test message",
            choiceIndex: 0,
            modelId: "testModel",
            toolCallUpdates: [],
            metadata: new Dictionary<string, object?>() { ["test-index"] = "test-value" });

        // Assert
        Assert.Equal("test message", Encoding.UTF8.GetString(content.ToByteArray()));
    }

    /*
    [Theory]
    [MemberData(nameof(InvalidChoices))]
    public void ConstructorWithInvalidChoiceSetsNullContent(object choice)
    {
        // Arrange
        var streamingChoice = choice as ChatWithDataStreamingChoice;

        // Act
        var content = new AzureOpenAIWithDataStreamingChatMessageContent(streamingChoice!, 0, "model-id");

        // Assert
        Assert.Null(content.Content);
    }

    public static IEnumerable<object[]> ValidChoices
    {
        get
        {
            yield return new object[] { new ChatWithDataStreamingChoice { Messages = [new() { Delta = new() { Content = "Content 1" } }] }, "Content 1" };
            yield return new object[] { new ChatWithDataStreamingChoice { Messages = [new() { Delta = new() { Content = "Content 2", Role = "Assistant" } }] }, "Content 2" };
        }
    }

    public static IEnumerable<object[]> InvalidChoices
    {
        get
        {
            yield return new object[] { new ChatWithDataStreamingChoice { Messages = [new() { EndTurn = true }] } };
            yield return new object[] { new ChatWithDataStreamingChoice { Messages = [new() { Delta = new() { Content = "Content", Role = "tool" } }] } };
        }
    }*/
}
