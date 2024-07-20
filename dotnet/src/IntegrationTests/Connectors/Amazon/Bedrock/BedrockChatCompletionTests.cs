// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Amazon;
using Connectors.Amazon.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Amazon;
using Microsoft.SemanticKernel.ChatCompletion;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Amazon.Bedrock;

public class BedrockChatCompletionTests
{
    [Theory]
    [InlineData("amazon.titan-text-premier-v1:0")]
    [InlineData("anthropic.claude-3-sonnet-20240229-v1:0")]
    [InlineData("anthropic.claude-3-haiku-20240307-v1:0")]
    [InlineData("anthropic.claude-v2:1")]
    [InlineData("ai21.jamba-instruct-v1:0")]
    [InlineData("cohere.command-r-plus-v1:0")]
    [InlineData("meta.llama3-8b-instruct-v1:0")]
    [InlineData("mistral.mistral-7b-instruct-v0:2")]
    public async Task ChatGenerationReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Alexa, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("What is 2 + 2?");

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, RegionEndpoint.USEast1).Build();
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var response = await chatCompletionService.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
        string output = "";
        foreach (var message in response)
        {
            output += message.Content;
            Console.WriteLine($"Chat Completion Answer: {message.Content}");
            Console.WriteLine();
        }

        // Assert
        Assert.NotNull(output);
        Assert.True(output.Contains('4', StringComparison.OrdinalIgnoreCase) || output.Contains("four", StringComparison.OrdinalIgnoreCase));
    }

    [Theory]
    [InlineData("mistral.mistral-7b-instruct-v0:2")]
    [InlineData("amazon.titan-text-premier-v1:0")]
    [InlineData("anthropic.claude-v2")]
    [InlineData("anthropic.claude-3-sonnet-20240229-v1:0")]
    [InlineData("cohere.command-r-plus-v1:0")]
    [InlineData("meta.llama3-8b-instruct-v1:0")]
    public async Task CharStreamingReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Alexa, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("What is 2 + 2?");

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, RegionEndpoint.USEast1).Build();
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var response = chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
        string output = "";
        await foreach (var message in response)
        {
            output += message.Content;
            Console.WriteLine($"Chat Completion Answer: {message.Content}");
            Console.WriteLine();
        }

        // Assert
        Assert.NotNull(output);
        Assert.True(output.Contains('4', StringComparison.OrdinalIgnoreCase) || output.Contains("four", StringComparison.OrdinalIgnoreCase));
    }
}
