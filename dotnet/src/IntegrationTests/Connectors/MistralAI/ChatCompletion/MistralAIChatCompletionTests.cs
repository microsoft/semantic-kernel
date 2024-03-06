// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MistralAI;

/// <summary>
/// Integration tests for <see cref="MistralAIChatCompletionService"/>.
/// </summary>
public sealed class MistralAIChatCompletionTests
{
    private readonly IConfigurationRoot _configuration;

    public MistralAIChatCompletionTests()
    {
        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<MistralAIChatCompletionTests>()
            .Build();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task MistralAIChatCompletionTestsAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:ChatModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAIChatCompletionService(model!, apiKey!);

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.True(response[0].Content?.Length > 0);
    }
}
