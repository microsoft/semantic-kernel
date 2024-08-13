// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureAIInference;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.AzureAIInference;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class AzureAIInferenceChatCompletionServiceTests(ITestOutputHelper output) : IDisposable
{
    private readonly XunitLogger<Kernel> _loggerFactory = new(output);
    private readonly RedirectOutput _testOutputHelper = new(output);
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureAIInferenceChatCompletionServiceTests>()
        .Build();

    [Theory]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task InvokeGetChatMessageContentsAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        var config = this._configuration.GetSection("AzureAIInference").Get<AzureAIInferenceConfiguration>();
        Assert.NotNull(config);

        var sut = new AzureAIInferenceChatCompletionService(
            endpoint: config.Endpoint,
            apiKey: config.ApiKey,
            loggerFactory: this._loggerFactory);

        ChatHistory chatHistory = [
            new ChatMessageContent(AuthorRole.User, prompt)
        ];

        // Act
        var result = await sut.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.Single(result);
        Assert.Contains(expectedAnswerContains, result[0].Content, StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task InvokeGetStreamingChatMessageContentsAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        var config = this._configuration.GetSection("AzureAIInference").Get<AzureAIInferenceConfiguration>();
        Assert.NotNull(config);

        var sut = new AzureAIInferenceChatCompletionService(
            endpoint: config.Endpoint,
            apiKey: config.ApiKey,
            loggerFactory: this._loggerFactory);

        ChatHistory chatHistory = [
            new ChatMessageContent(AuthorRole.User, prompt)
        ];

        StringBuilder fullContent = new();

        // Act
        await foreach (var update in sut.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            fullContent.Append(update.Content);
        };

        // Assert
        Assert.Contains(expectedAnswerContains, fullContent.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    public void Dispose()
    {
        this._loggerFactory.Dispose();
        this._testOutputHelper.Dispose();
    }
}
