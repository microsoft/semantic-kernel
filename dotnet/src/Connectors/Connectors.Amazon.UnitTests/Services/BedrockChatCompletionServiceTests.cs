// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Endpoints;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Amazon.UnitTests;

/// <summary>
/// Unit tests for Bedrock Chat Completion Service.
/// </summary>
public sealed class BedrockChatCompletionServiceTests
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
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Assert
        Assert.Equal(modelId, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    /// <summary>
    /// Checks that an invalid model ID cannot create a new service.
    /// </summary>
    [Fact]
    public void ShouldThrowExceptionForInvalidModelId()
    {
        // Arrange
        string invalidModelId = "invalid_model_id";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();

        // Act
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(invalidModelId, mockBedrockApi.Object).Build();

        // Assert
        Assert.Throws<KernelException>(() =>
            kernel.GetRequiredService<IChatCompletionService>());
    }

    /// <summary>
    /// Checks that an empty model ID cannot create a new service.
    /// </summary>
    [Fact]
    public void ShouldThrowExceptionForEmptyModelId()
    {
        // Arrange
        string emptyModelId = string.Empty;
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();

        // Act
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(emptyModelId, mockBedrockApi.Object).Build();

        // Assert
        Assert.Throws<KernelException>(() =>
            kernel.GetRequiredService<IChatCompletionService>());
    }

    /// <summary>
    /// Checks that an invalid BedrockRuntime object will throw an exception.
    /// </summary>
    [Fact]
    public async Task ShouldThrowExceptionForNullBedrockRuntimeAsync()
    {
        // Arrange
        string modelId = "mistral.mistral-text-lite-v1";
        IAmazonBedrockRuntime? nullBedrockRuntime = null;
        var chatHistory = CreateSampleChatHistory();

        // Act & Assert
        await Assert.ThrowsAnyAsync<Exception>(async () =>
        {
            var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, nullBedrockRuntime).Build();
            var service = kernel.GetRequiredService<IChatCompletionService>();
            await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
        }).ConfigureAwait(true);
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
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("Hello, world!", ConversationRole.Assistant));
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        Assert.Single(result);
        Assert.Equal(AuthorRole.Assistant, result[0].Role);
        Assert.Single(result[0].Items);
        Assert.Equal("Hello, world!", result[0].Items[0].ToString());
        Assert.NotNull(result[0].InnerContent);
    }

    /// <summary>
    /// Checks that GetStreamingChatMessageContentsAsync calls and correctly handles outputs from ConverseStreamAsync.
    /// </summary>
    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncShouldReturnStreamedChatMessageContentsAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-lite-v1";

        var content = this.GetTestResponseAsBytes("converse_stream_binary_response.bin");
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseStreamRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
#pragma warning disable CA2000 // Dispose objects before losing scope
        mockBedrockApi.Setup(m => m.ConverseStreamAsync(It.IsAny<ConverseStreamRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ConverseStreamResponse
            {
                Stream = new ConverseStreamOutput(new MemoryStream(content))
            });
#pragma warning restore CA2000 // Dispose objects before losing scope

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        List<StreamingChatMessageContent> output = new();
        var result = service.GetStreamingChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        int iterations = 0;
        await foreach (var item in result)
        {
            iterations += 1;
            Assert.NotNull(item);
            Assert.NotNull(item.Content);
            Assert.NotNull(item.Role);
            Assert.NotNull(item.InnerContent);
            output.Add(item);
        }
        Assert.True(output.Count > 0);
        Assert.Equal(iterations, output.Count);
        Assert.NotNull(service.GetModelId());
        Assert.NotNull(service.Attributes);
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
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("Hello, world!", ConversationRole.Assistant));
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
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
    /// Checks that the chat history is given the correct values through calling GetChatMessageContentsAsync.
    /// </summary>
    [Fact]
    public async Task GetChatMessageContentsAsyncShouldHaveProperChatHistoryAsync()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });

        // Set up the mock ConverseAsync to return multiple responses
        mockBedrockApi.SetupSequence(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("I'm doing well.", ConversationRole.Assistant))
            .ReturnsAsync(this.CreateConverseResponse("That's great to hear!", ConversationRole.User));

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
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
        Assert.Equal(6, chatHistory.Count); // Use the Count property to get the number of messages

        Assert.Equal(AuthorRole.User, chatHistory[0].Role); // Use the indexer to access individual messages
        Assert.Equal("Hello", chatHistory[0].Items[0].ToString());

        Assert.Equal(AuthorRole.Assistant, chatHistory[1].Role);
        Assert.Equal("Hi", chatHistory[1].Items[0].ToString());

        Assert.Equal(AuthorRole.User, chatHistory[2].Role);
        Assert.Equal("How are you?", chatHistory[2].Items[0].ToString());

        Assert.Equal(AuthorRole.System, chatHistory[3].Role);
        Assert.Equal("You are an AI Assistant", chatHistory[3].Items[0].ToString());

        Assert.Equal(AuthorRole.Assistant, chatHistory[4].Role);
        Assert.Equal("I'm doing well.", chatHistory[4].Items[0].ToString());

        Assert.Equal(AuthorRole.User, chatHistory[5].Role);
        Assert.Equal("That's great to hear!", chatHistory[5].Items[0].ToString());
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
            .ReturnsAsync(this.CreateConverseResponse("hi", ConversationRole.Assistant));
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(
            () => service.GetChatMessageContentsAsync(chatHistory)).ConfigureAwait(true);
    }

    /// <summary>
    /// Checks error handling for empty response output.
    /// </summary>
    [Fact]
    public async Task ShouldHandleInvalidConverseResponseAsync()
    {
        // Arrange
        string modelId = "anthropic.claude-chat-completion";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ConverseResponse
            {
                Output = new ConverseOutput
                {
                    Message = null // Invalid response, missing message
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            service.GetChatMessageContentsAsync(chatHistory)).ConfigureAwait(true);
    }

    /// <summary>
    /// Checks error handling for invalid role mapping.
    /// </summary>
    [Fact]
    public async Task ShouldHandleInvalidRoleMappingAsync()
    {
        // Arrange
        string modelId = "anthropic.claude-chat-completion";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("Hello", (ConversationRole)"bad_role"));
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() =>
            service.GetChatMessageContentsAsync(chatHistory)).ConfigureAwait(true);
    }

    /// <summary>
    /// Checks that the chat history is correctly handled when there are null or empty messages in the chat history, but not as the last message.
    /// </summary>
    [Fact]
    public async Task ShouldHandleEmptyChatHistoryMessagesAsync()
    {
        // Arrange
        string modelId = "anthropic.claude-chat-completion";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("hello", ConversationRole.Assistant));
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(string.Empty); // Add an empty user message
        chatHistory.AddAssistantMessage(null!); // Add a null assistant message
        chatHistory.AddUserMessage("Hi");

        // Act & Assert
        await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
        // Ensure that the method handles empty messages gracefully (e.g., by skipping them)
        // and doesn't throw an exception
    }

    private static ChatHistory CreateSampleChatHistory()
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("How are you?");
        chatHistory.AddSystemMessage("You are an AI Assistant");
        return chatHistory;
    }

    private byte[] GetTestResponseAsBytes(string fileName)
    {
        return File.ReadAllBytes($"TestData/{fileName}");
    }

    private ConverseResponse CreateConverseResponse(string text, ConversationRole role)
    {
        return new ConverseResponse
        {
            Output = new ConverseOutput
            {
                Message = new Message
                {
                    Role = role,
                    Content = new List<ContentBlock> { new() { Text = text } }
                }
            },
            Metrics = new ConverseMetrics(),
            StopReason = StopReason.Max_tokens,
            Usage = new TokenUsage()
        };
    }
}
