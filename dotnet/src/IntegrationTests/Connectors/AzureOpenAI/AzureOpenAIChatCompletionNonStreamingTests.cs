// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
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

public sealed class AzureOpenAIChatCompletionNonStreamingTests : BaseIntegrationTest
{
    [Fact]
    public async Task ChatCompletionShouldUseChatSystemPromptAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var chatCompletion = kernel.Services.GetRequiredService<IChatCompletionService>();

        var settings = new AzureOpenAIPromptExecutionSettings { ChatSystemPrompt = "Reply \"I don't know\" to every question." };

        // Act
        var result = await chatCompletion.GetChatMessageContentAsync("What is the capital of France?", settings, kernel);

        // Assert
        Assert.Contains("I don't know", result.Content);
    }

    [Fact]
    public async Task ChatCompletionShouldUseChatHistoryAndReturnMetadataAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var chatCompletion = kernel.Services.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory("Reply \"I don't know\" to every question.");
        chatHistory.AddUserMessage("What is the capital of France?");

        // Act
        var result = await chatCompletion.GetChatMessageContentAsync(chatHistory, null, kernel);

        // Assert
        Assert.Contains("I don't know", result.Content);
        Assert.NotNull(result.Metadata);

        Assert.True(result.Metadata.TryGetValue("Id", out object? id));
        Assert.NotNull(id);

        Assert.True(result.Metadata.TryGetValue("CreatedAt", out object? createdAt));
        Assert.NotNull(createdAt);

        Assert.True(result.Metadata.ContainsKey("SystemFingerprint"));

        Assert.True(result.Metadata.TryGetValue("Usage", out object? usageObject));
        Assert.NotNull(usageObject);

        var jsonObject = JsonSerializer.SerializeToElement(usageObject);
        Assert.True(jsonObject.TryGetProperty("InputTokens", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("OutputTokens", out JsonElement completionTokensJson));
        Assert.True(jsonObject.TryGetProperty("InputTokenCount", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("OutputTokenCount", out JsonElement completionTokensJson));
        Assert.True(jsonObject.TryGetProperty("InputTokenCount", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("OutputTokenCount", out JsonElement completionTokensJson));
        Assert.True(completionTokensJson.TryGetInt32(out int completionTokens));
        Assert.NotEqual(0, completionTokens);

        Assert.True(result.Metadata.TryGetValue("FinishReason", out object? finishReason));
        Assert.Equal("Stop", finishReason);

        Assert.True(result.Metadata.TryGetValue("ContentTokenLogProbabilities", out object? logProbabilityInfo));
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityInfo>)!);
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityInfo>)!);
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityDetails>)!);
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityDetails>)!);
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityDetails>)!);
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityDetails>)!);
    }

    [Fact]
    public async Task TextGenerationShouldUseChatSystemPromptAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var textGeneration = kernel.Services.GetRequiredService<ITextGenerationService>();

        var settings = new AzureOpenAIPromptExecutionSettings { ChatSystemPrompt = "Reply \"I don't know\" to every question." };

        // Act
        var result = await textGeneration.GetTextContentAsync("What is the capital of France?", settings, kernel);

        // Assert
        Assert.Contains("I don't know", result.Text);
    }

    [Fact]
    public async Task TextGenerationShouldReturnMetadataAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var textGeneration = kernel.Services.GetRequiredService<ITextGenerationService>();

        // Act
        var result = await textGeneration.GetTextContentAsync("Reply \"I don't know\" to every question. What is the capital of France?", null, kernel);

        // Assert
        Assert.Contains("I don't know", result.Text);
        Assert.NotNull(result.Metadata);

        Assert.True(result.Metadata.TryGetValue("Id", out object? id));
        Assert.NotNull(id);

        Assert.True(result.Metadata.TryGetValue("CreatedAt", out object? createdAt));
        Assert.NotNull(createdAt);

        Assert.True(result.Metadata.ContainsKey("SystemFingerprint"));

        Assert.True(result.Metadata.TryGetValue("Usage", out object? usageObject));
        Assert.NotNull(usageObject);

        var jsonObject = JsonSerializer.SerializeToElement(usageObject);
        Assert.True(jsonObject.TryGetProperty("InputTokens", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("OutputTokens", out JsonElement completionTokensJson));
        Assert.True(jsonObject.TryGetProperty("InputTokenCount", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("OutputTokenCount", out JsonElement completionTokensJson));
        Assert.True(jsonObject.TryGetProperty("InputTokenCount", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("OutputTokenCount", out JsonElement completionTokensJson));
        Assert.True(completionTokensJson.TryGetInt32(out int completionTokens));
        Assert.NotEqual(0, completionTokens);

        Assert.True(result.Metadata.TryGetValue("FinishReason", out object? finishReason));
        Assert.Equal("Stop", finishReason);

        Assert.True(result.Metadata.TryGetValue("ContentTokenLogProbabilities", out object? logProbabilityInfo));
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityInfo>)!);
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityInfo>)!);
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityDetails>)!);
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityDetails>)!);
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityDetails>)!);
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityDetails>)!);
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
