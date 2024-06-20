// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.HuggingFace.ChatCompletion;

/// <summary>
/// Integration tests for <see cref="HuggingFaceChatCompletionService"/>.
/// </summary>
public sealed class HuggingFaceChatCompletionTests
{
    private const string Endpoint = "https://<your-deployment>.endpoints.huggingface.cloud/v1/";
    private const string Model = "tgi";

    private readonly IConfigurationRoot _configuration;

    public HuggingFaceChatCompletionTests()
    {
        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<HuggingFaceChatCompletionTests>()
            .Build();
    }

    [Fact] // (Skip = "This test is for manual verification.")
    public async Task HuggingFaceRemoteChatCompletionAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.System, "Use C# 12 features."),
            new ChatMessageContent(AuthorRole.User, "Write a C# Hello world?")
        };
        var huggingFaceRemote = new HuggingFaceChatCompletionService(Model, endpoint: new Uri(Endpoint), apiKey: this.GetApiKey());

        // Act
        var response = await huggingFaceRemote.GetChatMessageContentsAsync(chatHistory, new HuggingFacePromptExecutionSettings() { MaxNewTokens = 50 });

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.True(response[0].Content?.Length > 0);
    }

    [Fact] // (Skip = "This test is for manual verification.")
    public async Task RunKernelFunctionWithHuggingFaceShouldRunCorrectlyAsync()
    {
        Kernel kernel = Kernel.CreateBuilder()
            .AddHuggingFaceChatCompletion(Model, endpoint: new Uri(Endpoint), apiKey: this.GetApiKey())
            .Build();

        var kernelFunction = kernel.CreateFunctionFromPrompt("Write a C# Hello world", new HuggingFacePromptExecutionSettings
        {
            Temperature = 0.4f,
            TopP = 1
        });

        await foreach (var update in kernel.InvokeStreamingAsync<StreamingChatMessageContent>(kernelFunction))
        {
            if (update.Content is { Length: > 0 })
            {
                Console.Write(update.Content);
            }
        }
    }

    private string GetApiKey()
    {
        return this._configuration.GetSection("HuggingFace:ApiKey").Get<string>()!;
    }
}
