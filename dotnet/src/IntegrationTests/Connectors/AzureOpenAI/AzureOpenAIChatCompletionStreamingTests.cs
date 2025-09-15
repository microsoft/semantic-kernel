// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.TextGeneration;
using OpenAI.Chat;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureOpenAI;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class AzureOpenAIChatCompletionStreamingTests : BaseIntegrationTest
{
    [Fact]
    public async Task ChatCompletionShouldUseChatSystemPromptAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var chatCompletion = kernel.Services.GetRequiredService<IChatCompletionService>();

        var settings = new AzureOpenAIPromptExecutionSettings { ChatSystemPrompt = "Reply \"I don't know\" to every question." };

        var stringBuilder = new StringBuilder();

        // Act
        await foreach (var update in chatCompletion.GetStreamingChatMessageContentsAsync("What is the capital of France?", settings, kernel))
        {
            stringBuilder.Append(update.Content);
        }

        // Assert
        Assert.Contains("I don't know", stringBuilder.ToString());
    }

    [Fact]
    public async Task ChatCompletionShouldUseChatHistoryAndReturnMetadataAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var chatCompletion = kernel.Services.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory("Reply \"I don't know\" to every question.");
        chatHistory.AddUserMessage("What is the capital of France?");

        var stringBuilder = new StringBuilder();
        var metadata = new Dictionary<string, object?>();
        var hasUsage = false;

        // Act & Assert
        await foreach (var update in chatCompletion.GetStreamingChatMessageContentsAsync(chatHistory, null, kernel))
        {
            stringBuilder.Append(update.Content);

            var openAIUpdate = Assert.IsType<StreamingChatCompletionUpdate>(update.InnerContent);
            Assert.NotNull(openAIUpdate);

            if (openAIUpdate.Usage is not null)
            {
                Assert.True(openAIUpdate.Usage.TotalTokenCount > 0);
                hasUsage = true;
            }

            foreach (var key in update.Metadata!.Keys)
            {
                if (!metadata.TryGetValue(key, out object? value) || value is null)
                {
                    metadata[key] = update.Metadata[key];
                }
            }
        }

        Assert.True(hasUsage);
        Assert.Contains("I don't know", stringBuilder.ToString());
        Assert.NotNull(metadata);

        Assert.True(metadata.TryGetValue("CompletionId", out object? id));
        Assert.NotNull(id);

        Assert.True(metadata.TryGetValue("CreatedAt", out object? createdAt));
        Assert.NotNull(createdAt);

        Assert.True(metadata.ContainsKey("SystemFingerprint"));

        Assert.True(metadata.TryGetValue("FinishReason", out object? finishReason));
        Assert.Equal("Stop", finishReason);
    }

    [Fact]
    public async Task TextGenerationShouldUseChatSystemPromptAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var textGeneration = kernel.Services.GetRequiredService<ITextGenerationService>();

        var settings = new AzureOpenAIPromptExecutionSettings { ChatSystemPrompt = "Reply \"I don't know\" to every question." };

        var stringBuilder = new StringBuilder();

        // Act
        await foreach (var update in textGeneration.GetStreamingTextContentsAsync("What is the capital of France?", settings, kernel))
        {
            stringBuilder.Append(update);
        }

        // Assert
        Assert.Contains("I don't know", stringBuilder.ToString());
    }

    [Fact]
    public async Task TextGenerationShouldReturnMetadataAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var textGeneration = kernel.Services.GetRequiredService<ITextGenerationService>();

        // Act
        var stringBuilder = new StringBuilder();
        var metadata = new Dictionary<string, object?>();

        // Act
        await foreach (var update in textGeneration.GetStreamingTextContentsAsync("What is the capital of France?", null, kernel))
        {
            stringBuilder.Append(update);

            foreach (var key in update.Metadata!.Keys)
            {
                if (!metadata.TryGetValue(key, out object? value) || value is null)
                {
                    metadata[key] = update.Metadata[key];
                }
            }
        }

        // Assert
        Assert.NotNull(metadata);

        Assert.True(metadata.TryGetValue("CompletionId", out object? id));
        Assert.NotNull(id);

        Assert.True(metadata.TryGetValue("CreatedAt", out object? createdAt));
        Assert.NotNull(createdAt);

        Assert.True(metadata.ContainsKey("SystemFingerprint"));

        Assert.True(metadata.TryGetValue("FinishReason", out object? finishReason));
        Assert.Equal("Stop", finishReason);
    }

    #region internals

    private Kernel CreateAndInitializeKernel()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            credentials: new AzureCliCredential());

        return kernelBuilder.Build();
    }

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureOpenAIChatCompletionTests>()
        .Build();

    #endregion
}
