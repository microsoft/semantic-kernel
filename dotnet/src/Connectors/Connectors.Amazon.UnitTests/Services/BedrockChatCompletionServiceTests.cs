// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Services;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace Connectors.Amazon.UnitTests.Services;

/// <summary>
/// Unit tests for Bedrock Chat Completion Service.
/// </summary>
public class BedrockChatCompletionServiceTests
{
    /// <summary>
    /// Checks that modelID is added to the list of service attributes when service is registered.
    /// </summary>
    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        string modelId = "amazon.titan-text-premier-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var service = new BedrockChatCompletionService(modelId, mockBedrockApi.Object);

        // Assert
        Assert.Equal(modelId, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }
    /// <summary>
    /// Checks that GetChatMessageContentsAsync calls and correctly handles outputs from ConverseAsync.
    /// </summary>
    [Fact]
    public async Task GetChatMessageContentsAsyncShouldReturnChatMessageContentsAsync()
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
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        Assert.Single(result);
        Assert.Equal(AuthorRole.Assistant, result[0].Role);
        Assert.Single(result[0].Items);
        Assert.Equal("Hello, world!", result[0].Items[0].ToString());
    }
    /// <summary>
    /// Checks that GetStreamingChatMessageContentsAsync calls and correctly handles outputs from ConverseStreamAsync.
    /// </summary>
    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncShouldReturnStreamedChatMessageContentsAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();

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
    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the chat completion call.
    /// </summary>
    [Fact]
    public async Task TitanGetChatMessageContentsAsyncShouldReturnChatMessageWithPromptExecutionSettingsAsync()
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
        ConverseRequest converseRequest = new ConverseRequest();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        if (invocation != null)
        {
            converseRequest = (ConverseRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.ExtensionData["temperature"], converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.ExtensionData["topP"], converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.ExtensionData["maxTokenCount"], converseRequest?.InferenceConfig.MaxTokens);
    }
    /// <summary>
    /// Checks that the roles from the chat history are correctly assigned and labeled for the converse calls.
    /// </summary>
    [Fact]
    public async Task GetChatMessageContentsAsyncShouldAssignCorrectRolesAsync()
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
    /// <summary>
    /// Checks that the chat history is given the correct values through calling GetChatMessageContentsAsync.
    /// </summary>
    [Fact]
    public async Task GetChatMessageContentsAsyncShouldHaveProperChatHistoryAsync()
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
        string? chatResult1 = result1[0].Content;
        Assert.NotNull(chatResult1);
        chatHistory.AddAssistantMessage(chatResult1);
        string? chatResult2 = result2[0].Content;
        Assert.NotNull(chatResult2);
        chatHistory.AddUserMessage(chatResult2);
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
    /// <summary>
    /// Checks that error handling present for empty chat history.
    /// </summary>
    [Fact]
    public async Task ShouldThrowArgumentExceptionIfChatHistoryIsEmptyAsync()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var chatHistory = new ChatHistory();
        mockBedrockApi.SetupSequence(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ConverseResponse
            {
                Output = new ConverseOutput
                {
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = new List<ContentBlock> { new ContentBlock { Text = "sample" } }
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var service = new BedrockChatCompletionService(modelId, mockBedrockApi.Object);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(
            () => service.GetChatMessageContentsAsync(chatHistory)).ConfigureAwait(true);
    }
    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the chat completion call.
    /// </summary>
    [Fact]
    public async Task ClaudeGetChatMessageContentsAsyncShouldReturnChatMessageWithPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "anthropic.claude-chat-completion";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.7f },
                { "top_p", 0.7f },
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
        ConverseRequest converseRequest = new ConverseRequest();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        if (invocation != null)
        {
            converseRequest = (ConverseRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.ExtensionData["temperature"], converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.ExtensionData["top_p"], converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.ExtensionData["maxTokenCount"], converseRequest?.InferenceConfig.MaxTokens);
    }
    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the chat completion call.
    /// </summary>
    [Fact]
    public async Task LlamaGetChatMessageContentsAsyncShouldReturnChatMessageWithPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "meta.llama3-text-lite-v1";
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
        ConverseRequest converseRequest = new ConverseRequest();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        if (invocation != null)
        {
            converseRequest = (ConverseRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.ExtensionData["temperature"], converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.ExtensionData["topP"], converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.ExtensionData["maxTokenCount"], converseRequest?.InferenceConfig.MaxTokens);
    }
    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the chat completion call.
    /// </summary>
    [Fact]
    public async Task MistralGetChatMessageContentsAsyncShouldReturnChatMessageWithPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "mistral.mistral-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.5f },
                { "top_p", .9f },
                { "max_tokens", 512 }
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
        ConverseRequest converseRequest = new ConverseRequest();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        if (invocation != null)
        {
            converseRequest = (ConverseRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.ExtensionData["temperature"], converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.ExtensionData["top_p"], converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.ExtensionData["max_tokens"], converseRequest?.InferenceConfig.MaxTokens);
    }
    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the chat completion call.
    /// </summary>
    [Fact]
    public async Task CommandRGetChatMessageContentsAsyncShouldReturnChatMessageWithPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "cohere.command-r-chat-stuff";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.7f },
                { "p", 0.9f },
                { "max_tokens", 202 }
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
        ConverseRequest converseRequest = new ConverseRequest();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        if (invocation != null)
        {
            converseRequest = (ConverseRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.ExtensionData["temperature"], converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.ExtensionData["p"], converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.ExtensionData["max_tokens"], converseRequest?.InferenceConfig.MaxTokens);
    }
    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the chat completion call.
    /// </summary>
    [Fact]
    public async Task JambaGetChatMessageContentsAsyncShouldReturnChatMessageWithPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "ai21.jamba-chat-stuff";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new PromptExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.7f },
                { "top_p", 0.9f },
                { "max_tokens", 202 }
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
        ConverseRequest converseRequest = new ConverseRequest();
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        if (invocation != null)
        {
            converseRequest = (ConverseRequest)invocation.Arguments[0];
        }
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.ExtensionData["temperature"], converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.ExtensionData["top_p"], converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.ExtensionData["max_tokens"], converseRequest?.InferenceConfig.MaxTokens);
    }
}
