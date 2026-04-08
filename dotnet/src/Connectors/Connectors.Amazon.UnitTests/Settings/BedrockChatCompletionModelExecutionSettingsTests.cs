// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Endpoints;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Amazon.UnitTests;

/// <summary>
/// Unit tests for prompt execution settings confirgurations for different Bedrock Models.
/// </summary>
public class BedrockChatCompletionModelExecutionSettingsTests
{
    /// <summary>
    /// Checks that an invalid prompt execution settings will throw an exception.
    /// </summary>
    [Fact]
    public async Task ShouldThrowExceptionForInvalidPromptExecutionSettingsAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        var invalidSettings = new AmazonTitanExecutionSettings()
        {
            Temperature = -1.0f,
            TopP = -0.5f,
            MaxTokenCount = -100
        };
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            service.GetChatMessageContentsAsync(chatHistory, invalidSettings)).ConfigureAwait(true);
    }
    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the chat completion call.
    /// </summary>
    [Fact]
    public async Task ExecutionSettingsExtensionDataShouldOverridePropertyAsync()
    {
        // Arrange
        string modelId = "mistral.mistral-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonMistralExecutionSettings()
        {
            Temperature = 0.0f,
            TopP = 0.0f,
            MaxTokens = 10,
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.5f },
                { "top_p", 0.9f },
                { "max_tokens", 512 }
            }
        };
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
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = [new() { Text = "I'm doing well." }]
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, executionSettings).ConfigureAwait(true);

        // Assert
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        Assert.NotNull(invocation);
        ConverseRequest converseRequest = (ConverseRequest)invocation.Arguments[0];
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.NotEqual(executionSettings.Temperature, converseRequest?.InferenceConfig.Temperature);
        Assert.NotEqual(executionSettings.TopP, converseRequest?.InferenceConfig.TopP);
        Assert.NotEqual(executionSettings.MaxTokens, converseRequest?.InferenceConfig.MaxTokens);
        Assert.Equal(executionSettings.ExtensionData["temperature"], converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.ExtensionData["top_p"], converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.ExtensionData["max_tokens"], converseRequest?.InferenceConfig.MaxTokens);
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the chat completion call.
    /// </summary>
    [Fact]
    public async Task TitanExecutionSettingsShouldSetExtensionDataAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonTitanExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.3f },
                { "topP", 0.8f },
                { "maxTokenCount", 510 }
            }
        };
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
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = [new() { Text = "I'm doing well." }]
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, executionSettings).ConfigureAwait(true);

        // Assert
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        Assert.NotNull(invocation);
        ConverseRequest converseRequest = (ConverseRequest)invocation.Arguments[0];
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
    public async Task TitanExecutionSettingsShouldSetPropertiesAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-lite-v1";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonTitanExecutionSettings()
        {
            Temperature = 0.3f,
            TopP = 0.8f,
            MaxTokenCount = 510,
            ModelId = modelId
        };
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
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = [new() { Text = "I'm doing well." }]
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, executionSettings).ConfigureAwait(true);

        // Assert
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        Assert.NotNull(invocation);
        ConverseRequest converseRequest = (ConverseRequest)invocation.Arguments[0];
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.Temperature, converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.TopP, converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.MaxTokenCount, converseRequest?.InferenceConfig.MaxTokens);
    }

    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the chat completion call.
    /// </summary>
    [Fact]
    public async Task ClaudePromptExecutionSettingsExtensionDataSetsProperlyAsync()
    {
        // Arrange
        string modelId = "anthropic.claude-chat-completion";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonClaudeExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.7f },
                { "top_p", 0.7f },
                { "max_tokens_to_sample", 512 }
            }
        };
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
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = [new() { Text = "I'm doing well." }]
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, executionSettings).ConfigureAwait(true);

        // Assert
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        Assert.NotNull(invocation);
        ConverseRequest converseRequest = (ConverseRequest)invocation.Arguments[0];
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.ExtensionData["temperature"], converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.ExtensionData["top_p"], converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.ExtensionData["max_tokens_to_sample"], converseRequest?.InferenceConfig.MaxTokens);
    }
    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the chat completion call.
    /// </summary>
    [Fact]
    public async Task ClaudePromptExecutionSettingsSetsPropertiesAsync()
    {
        // Arrange
        string modelId = "anthropic.claude-chat-completion";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonClaudeExecutionSettings()
        {
            Temperature = 0.7f,
            TopP = 0.7f,
            MaxTokensToSample = 512,
            ModelId = modelId
        };
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
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = [new() { Text = "I'm doing well." }]
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, executionSettings).ConfigureAwait(true);

        // Assert
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        Assert.NotNull(invocation);
        ConverseRequest converseRequest = (ConverseRequest)invocation.Arguments[0];
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.Temperature, converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.TopP, converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.MaxTokensToSample, converseRequest?.InferenceConfig.MaxTokens);
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
                { "top_p", 0.6f },
                { "max_gen_len", 256 }
            }
        };
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
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = [new() { Text = "I'm doing well." }]
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, executionSettings).ConfigureAwait(true);

        // Assert
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        Assert.NotNull(invocation);
        ConverseRequest converseRequest = (ConverseRequest)invocation.Arguments[0];
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.ExtensionData["temperature"], converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.ExtensionData["top_p"], converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.ExtensionData["max_gen_len"], converseRequest?.InferenceConfig.MaxTokens);
    }
    /// <summary>
    /// Checks that the prompt execution settings are correctly registered for the chat completion call.
    /// </summary>
    [Fact]
    public async Task CommandRExecutionSettingsShouldSetExtensionDataAsync()
    {
        // Arrange
        string modelId = "cohere.command-r-chat-stuff";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonCommandRExecutionSettings()
        {
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.7f },
                { "p", 0.9f },
                { "max_tokens", 202 }
            }
        };
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
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = [new() { Text = "I'm doing well." }]
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, executionSettings).ConfigureAwait(true);

        // Assert
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        Assert.NotNull(invocation);
        ConverseRequest converseRequest = (ConverseRequest)invocation.Arguments[0];
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
    public async Task CommandRExecutionSettingsShouldSetPropertiesAsync()
    {
        // Arrange
        string modelId = "cohere.command-r-chat-stuff";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var executionSettings = new AmazonCommandRExecutionSettings()
        {
            Temperature = 0.7f,
            TopP = 0.9f,
            MaxTokens = 202,
            ModelId = modelId,
        };
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
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = [new() { Text = "I'm doing well." }]
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, executionSettings).ConfigureAwait(true);

        // Assert
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        Assert.NotNull(invocation);
        ConverseRequest converseRequest = (ConverseRequest)invocation.Arguments[0];
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.Temperature, converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.TopP, converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.MaxTokens, converseRequest?.InferenceConfig.MaxTokens);
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
        var executionSettings = new AmazonJambaExecutionSettings()
        {
            Temperature = 0.7f,
            ModelId = modelId,
            ExtensionData = new Dictionary<string, object>()
            {
                { "temperature", 0.7f },
                { "top_p", 0.9f },
                { "max_tokens", 202 }
            }
        };
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
                    Message = new Message
                    {
                        Role = ConversationRole.Assistant,
                        Content = [new() { Text = "I'm doing well." }]
                    }
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, executionSettings).ConfigureAwait(true);

        // Assert
        var invocation = mockBedrockApi.Invocations
            .Where(i => i.Method.Name == "ConverseAsync")
            .SingleOrDefault(i => i.Arguments.Count > 0 && i.Arguments[0] is ConverseRequest);
        Assert.NotNull(invocation);
        ConverseRequest converseRequest = (ConverseRequest)invocation.Arguments[0];
        Assert.Single(result);
        Assert.Equal("I'm doing well.", result[0].Items[0].ToString());
        Assert.Equal(executionSettings.ExtensionData["temperature"], converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.Temperature, converseRequest?.InferenceConfig.Temperature);
        Assert.Equal(executionSettings.ExtensionData["top_p"], converseRequest?.InferenceConfig.TopP);
        Assert.Equal(executionSettings.ExtensionData["max_tokens"], converseRequest?.InferenceConfig.MaxTokens);
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
}
