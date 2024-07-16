// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using System.Text.Json;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.EventStreams.Internal;
using Connectors.Amazon.Extensions;
using Connectors.Amazon.Services;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Connectors.Amazon.Services;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;
namespace Connectors.Amazon.UnitTests.Services;

public class BedrockChatCompletionServiceTests
{
    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var service = new BedrockChatCompletionService(modelId, mockBedrockApi.Object);

        // Assert
        Assert.Equal(modelId, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncShouldReturnChatMessageContents()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ConverseResponse
            {
                Output = new ConverseOutput
                {
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = new List<ContentBlock> { new ContentBlock { Text = "Hello, world!" } }
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var service = new BedrockChatCompletionService(modelId, mockBedrockApi.Object);
        var chatHistory = new ChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        Assert.Single(result);
        Assert.Equal(AuthorRole.Assistant, result[0].Role);
        Assert.Single(result[0].Items);
        Assert.Equal("Hello, world!", result[0].Items[0].ToString());
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncShouldReturnStreamedChatMessageContents()
    {
        // Arrange
        string modelId = "amazon.titan-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var events = new List<ContentBlockDeltaEvent>
        {
            new ContentBlockDeltaEvent
            {
                Delta = new ContentBlockDelta
                {
                    Text = "hello"
                }
            },
            new ContentBlockDeltaEvent
            {
                Delta = new ContentBlockDelta
                {
                    Text = " world"
                }
            }
        };
        var byteEvents = events.SelectMany(e => JsonSerializer.SerializeToUtf8Bytes(e)).ToArray();
        var memoryStream = new MemoryStream(byteEvents);

        mockBedrockApi.Setup(m => m.ConverseStreamAsync(It.IsAny<ConverseStreamRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ConverseStreamResponse
            {
                Stream = new ConverseStreamOutput(new MemoryStream())
            });

        var service = new BedrockChatCompletionService(modelId, mockBedrockApi.Object);
        var chatHistory = new ChatHistory();

        // Act
        List<StreamingChatMessageContent> output = new List<StreamingChatMessageContent>();
        var result = service.GetStreamingChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        await foreach (var item in result)
        {
            Assert.NotNull(item);
            Assert.NotNull(item.Content);
            Assert.NotNull(item.Role);
            output.Add(item);
        }
        Assert.NotNull(output);
        Assert.NotNull(service.GetModelId());
        Assert.NotNull(service.Attributes);
    }

    private static ChatHistory CreateSampleChatHistory()
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("How are you?");
        return chatHistory;
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncShouldUsePromptExecutionSettings()
    {
        // Arrange
        string modelId = "amazon.titan-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.7f },
                { "topP", 0.9f },
                { "maxTokenCount", 512 }
            }
        };
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ConverseResponse
            {
                Output = new ConverseOutput
                {
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = new List<ContentBlock> { new ContentBlock { Text = "I'm doing well." } }
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var service = new BedrockChatCompletionService(modelId, mockBedrockApi.Object);
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, executionSettings).ConfigureAwait(true);

        // Assert
        ConverseRequest converseRequest = null;
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        if (invocation != null)
        {
            converseRequest = (ConverseRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal(executionSettings.ExtensionData["temperature"], converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.ExtensionData["topP"], converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.ExtensionData["maxTokenCount"], converseRequest?.InferenceConfig.MaxTokens);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncShouldAssignCorrectRoles()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ConverseResponse
            {
                Output = new ConverseOutput
                {
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = new List<ContentBlock> { new ContentBlock { Text = "I'm doing well." } }
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var service = new BedrockChatCompletionService(modelId, mockBedrockApi.Object);
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        Assert.Single(result);
        Assert.Equal(AuthorRole.Assistant, result[0].Role);
        Assert.Single(result[0].Items);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncShouldHaveProperChatHistory()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();

        // Set up the mock ConverseAsync to return multiple responses
        mockBedrockApi.SetupSequence(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ConverseResponse
            {
                Output = new ConverseOutput
                {
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = new List<ContentBlock> { new ContentBlock { Text = "I'm doing well." } }
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            })
            .ReturnsAsync(new ConverseResponse
            {
                Output = new ConverseOutput
                {
                    Message = new Message
                    {
                        Role = ConversationRole.User,
                        Content = new List<ContentBlock> { new ContentBlock { Text = "That's great to hear!" } }
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });

        var service = new BedrockChatCompletionService(modelId, mockBedrockApi.Object);
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result1 = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
        var result2 = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        Assert.NotNull(result1[0].Content);
        chatHistory.AddAssistantMessage(result1[0].Content);
        Assert.NotNull(result2[0].Content);
        chatHistory.AddUserMessage(result2[0].Content);
        Assert.Equal(2, result1.Count + result2.Count);

        // Check the first result
        Assert.Equal(AuthorRole.Assistant, result1[0].Role);
        Assert.Single(result1[0].Items);
        Assert.Equal("I'm doing well.", result1[0].Items[0].ToString());

        // Check the second result
        Assert.Equal(AuthorRole.User, result2[0].Role);
        Assert.Single(result2[0].Items);
        Assert.Equal("That's great to hear!", result2[0].Items[0].ToString());

        // Check the chat history
        Assert.Equal(5, chatHistory.Count); // Use the Count property to get the number of messages
        Assert.Equal(AuthorRole.User, chatHistory[0].Role); // Use the indexer to access individual messages
        Assert.Equal("Hello", chatHistory[0].Items[0].ToString());
        Assert.Equal(AuthorRole.Assistant, chatHistory[1].Role);
        Assert.Equal("Hi", chatHistory[1].Items[0].ToString());
        Assert.Equal(AuthorRole.User, chatHistory[2].Role);
        Assert.Equal("How are you?", chatHistory[2].Items[0].ToString());
        Assert.Equal(AuthorRole.Assistant, chatHistory[3].Role);
        Assert.Equal("I'm doing well.", chatHistory[3].Items[0].ToString());
        Assert.Equal(AuthorRole.User, chatHistory[4].Role);
        Assert.Equal("That's great to hear!", chatHistory[4].Items[0].ToString());
    }
}
