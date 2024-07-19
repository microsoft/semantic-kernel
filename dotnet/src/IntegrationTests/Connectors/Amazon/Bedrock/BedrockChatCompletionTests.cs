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
    [Fact]
    public async Task ChatGenerationReturnsValidResponseAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Alexa, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("What is my name and what is 2 + 2?");

        string modelId = "amazon.titan-text-premier-v1:0";
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
        Assert.Contains("4", output, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Alexa", output, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task CharStreamingReturnsValidResponseAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Alexa, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("What is my name and what is 2 + 2?");

        string modelId = "amazon.titan-text-premier-v1:0";
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
        Assert.Contains("4", output, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("Alexa", output, StringComparison.OrdinalIgnoreCase);
    }
}
