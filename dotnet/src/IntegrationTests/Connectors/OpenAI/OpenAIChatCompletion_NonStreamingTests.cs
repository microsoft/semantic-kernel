// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextGeneration;
using OpenAI.Chat;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class OpenAIChatCompletionNonStreamingTests : BaseIntegrationTest
{
    [Fact]
    public async Task ChatCompletionShouldUseChatSystemPromptAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var chatCompletion = kernel.Services.GetRequiredService<IChatCompletionService>();

        var settings = new OpenAIPromptExecutionSettings { ChatSystemPrompt = "Reply \"I don't know\" to every question." };

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
        Assert.True(jsonObject.TryGetProperty("InputTokenCount", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("OutputTokenCount", out JsonElement completionTokensJson));
        Assert.True(completionTokensJson.TryGetInt32(out int completionTokens));
        Assert.NotEqual(0, completionTokens);

        Assert.True(result.Metadata.TryGetValue("FinishReason", out object? finishReason));
        Assert.Equal("Stop", finishReason);

        Assert.True(result.Metadata.TryGetValue("ContentTokenLogProbabilities", out object? logProbabilityInfo));
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityDetails>)!);
    }

    [Fact]
    public async Task TextGenerationShouldUseChatSystemPromptAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var textGeneration = kernel.Services.GetRequiredService<ITextGenerationService>();

        var settings = new OpenAIPromptExecutionSettings { ChatSystemPrompt = "Reply \"I don't know\" to every question." };

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
        Assert.True(jsonObject.TryGetProperty("InputTokenCount", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("OutputTokenCount", out JsonElement completionTokensJson));
        Assert.True(completionTokensJson.TryGetInt32(out int completionTokens));
        Assert.NotEqual(0, completionTokens);

        Assert.True(result.Metadata.TryGetValue("FinishReason", out object? finishReason));
        Assert.Equal("Stop", finishReason);

        Assert.True(result.Metadata.TryGetValue("ContentTokenLogProbabilities", out object? logProbabilityInfo));
        Assert.Empty((logProbabilityInfo as IReadOnlyList<ChatTokenLogProbabilityDetails>)!);
    }

    [Fact]
    public async Task ChatCompletionWithWebSearchAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(modelIdOverride: "gpt-4o-mini-search-preview");
        var chatService = kernel.Services.GetRequiredService<IChatCompletionService>();
        var settings = new OpenAIPromptExecutionSettings
        {
            WebSearchOptions = new ChatWebSearchOptions()
        };

        // Act
        var result = await chatService.GetChatMessageContentAsync("What are the top 3 trending news currently", settings, kernel);

        // Assert
        var chatCompletion = Assert.IsType<ChatCompletion>(result.InnerContent);
        Assert.NotNull(chatCompletion);
        Assert.NotEmpty(chatCompletion.Annotations);
    }

    [Fact]
    public async Task ChatCompletionWithAudioInputAndOutputAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(modelIdOverride: "gpt-4o-audio-preview");
        var chatService = kernel.Services.GetRequiredService<IChatCompletionService>();
        var settings = new OpenAIPromptExecutionSettings
        {
            Modalities = ChatResponseModalities.Audio | ChatResponseModalities.Text,
            Audio = new ChatAudioOptions(ChatOutputAudioVoice.Shimmer, ChatOutputAudioFormat.Mp3)
        };

        ChatHistory chatHistory = [];
        chatHistory.Add(new Microsoft.SemanticKernel.ChatMessageContent(AuthorRole.User, [
            new AudioContent(File.ReadAllBytes("TestData/test_audio.wav"), mimeType: "audio/wav")
        ]));

        // Act
        var result = await chatService.GetChatMessageContentAsync(chatHistory, settings);

        // Assert
        var audioContent = Assert.IsType<AudioContent>(result.Items.FirstOrDefault(i => i is AudioContent));
        Assert.NotNull(audioContent);
        Assert.NotNull(audioContent.Metadata);
        Assert.NotNull(audioContent.Metadata["Id"]);
        Assert.NotNull(audioContent.Metadata["ExpiresAt"]);
        Assert.NotNull(audioContent.Metadata["Transcript"]);
        Assert.Equal("audio/mp3", audioContent.MimeType);
        Assert.True(audioContent.Metadata.ContainsKey("Transcript"));
        Assert.NotNull(audioContent.Metadata["Transcript"]!);
        Assert.NotEmpty(audioContent.Metadata!["Transcript"]!.ToString()!);
    }

    #region internals

    private Kernel CreateAndInitializeKernel(string? modelIdOverride = null)
    {
        var OpenAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(OpenAIConfiguration);
        Assert.NotNull(modelIdOverride ?? OpenAIConfiguration.ChatModelId!);
        Assert.NotNull(OpenAIConfiguration.ApiKey);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddOpenAIChatCompletion(
            modelId: modelIdOverride ?? OpenAIConfiguration.ChatModelId!,
            apiKey: OpenAIConfiguration.ApiKey);

        return kernelBuilder.Build();
    }

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAIChatCompletionTests>()
        .Build();

    #endregion
}
