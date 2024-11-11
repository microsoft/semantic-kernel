// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextGeneration;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class OpenAIChatCompletionStreamingTests : BaseIntegrationTest
{
    [Fact]
    public async Task ChatCompletionShouldUseChatSystemPromptAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var chatCompletion = kernel.Services.GetRequiredService<IChatCompletionService>();

        var settings = new OpenAIPromptExecutionSettings { ChatSystemPrompt = "Reply \"I don't know\" to every question." };

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

        // Act
        await foreach (var update in chatCompletion.GetStreamingChatMessageContentsAsync(chatHistory, null, kernel))
        {
            stringBuilder.Append(update.Content);

            foreach (var key in update.Metadata!.Keys)
            {
                if (!metadata.TryGetValue(key, out var value) || value is null)
                {
                    metadata[key] = update.Metadata[key];
                }
            }
        }

        // Assert
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

        var settings = new OpenAIPromptExecutionSettings { ChatSystemPrompt = "Reply \"I don't know\" to every question." };

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
                if (!metadata.TryGetValue(key, out var value) || value is null)
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

    [Fact]
    public async Task RepeatedChatHistoryAddStreamingMessageWorksAsExpectedAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();
        var chatCompletion = kernel.Services.GetRequiredService<IChatCompletionService>();

        kernel.ImportPluginFromFunctions("TestFunctions",
        [
            kernel.CreateFunctionFromMethod((string input) => Task.FromResult(input), "Test", "Test executed.")
        ]);

        // Prepare Chat
        var chatService = kernel.GetRequiredService<IChatCompletionService>();

        OpenAIPromptExecutionSettings settings = new()
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        ChatHistory chatHistory = new("You are to test the system");

        for (int i = 0; i < 2; i++)
        {
            chatHistory.AddUserMessage("Please test the system");

            var results = chatHistory.AddStreamingMessageAsync(chatService
                .GetStreamingChatMessageContentsAsync(chatHistory, settings, kernel)
                .Cast<OpenAIStreamingChatMessageContent>()
            );

            await foreach (var result in results)
            {
                Console.Write(result.ToString());
            }

            Console.WriteLine($"Call #{i} OK");
        }
    }

    #region internals

    private Kernel CreateAndInitializeKernel()
    {
        var OpenAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(OpenAIConfiguration);
        Assert.NotNull(OpenAIConfiguration.ChatModelId!);
        Assert.NotNull(OpenAIConfiguration.ApiKey);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddOpenAIChatCompletion(
            modelId: OpenAIConfiguration.ChatModelId,
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
