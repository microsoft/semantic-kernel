// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Amazon;

public class BedrockChatCompletionTests
{
    [Theory(Skip = "For manual verification only")]
    [InlineData("ai21.jamba-instruct-v1:0")]
    [InlineData("amazon.titan-text-premier-v1:0")]
    [InlineData("amazon.titan-text-lite-v1")]
    [InlineData("amazon.titan-text-express-v1")]
    [InlineData("anthropic.claude-v2")]
    [InlineData("anthropic.claude-v2:1")]
    [InlineData("anthropic.claude-instant-v1")]
    [InlineData("anthropic.claude-3-sonnet-20240229-v1:0")]
    [InlineData("anthropic.claude-3-haiku-20240307-v1:0")]
    [InlineData("cohere.command-r-v1:0")]
    [InlineData("cohere.command-r-plus-v1:0")]
    [InlineData("meta.llama3-70b-instruct-v1:0")]
    [InlineData("meta.llama3-8b-instruct-v1:0")]
    [InlineData("mistral.mistral-7b-instruct-v0:2")]
    [InlineData("mistral.mistral-large-2402-v1:0")]
    [InlineData("mistral.mistral-small-2402-v1:0")]
    [InlineData("mistral.mixtral-8x7b-instruct-v0:1")]
    public async Task ChatCompletionReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Alexa, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("What is 2 + 2?");

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId).Build();
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var response = await chatCompletionService.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
        string output = "";
        foreach (var message in response)
        {
            output += message.Content;
            Assert.NotNull(message.InnerContent);
        }
        chatHistory.AddAssistantMessage(output);

        // Assert
        Assert.NotNull(output);
        Assert.True(response.Count > 0);
        Assert.Equal(4, chatHistory.Count);
        Assert.Equal(AuthorRole.Assistant, chatHistory[3].Role);
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("ai21.jamba-instruct-v1:0")]
    [InlineData("amazon.titan-text-premier-v1:0")]
    [InlineData("amazon.titan-text-lite-v1")]
    [InlineData("amazon.titan-text-express-v1")]
    [InlineData("anthropic.claude-v2")]
    [InlineData("anthropic.claude-v2:1")]
    [InlineData("anthropic.claude-instant-v1")]
    [InlineData("anthropic.claude-3-sonnet-20240229-v1:0")]
    [InlineData("anthropic.claude-3-haiku-20240307-v1:0")]
    [InlineData("cohere.command-r-v1:0")]
    [InlineData("cohere.command-r-plus-v1:0")]
    [InlineData("meta.llama3-70b-instruct-v1:0")]
    [InlineData("meta.llama3-8b-instruct-v1:0")]
    [InlineData("mistral.mistral-7b-instruct-v0:2")]
    [InlineData("mistral.mistral-large-2402-v1:0")]
    [InlineData("mistral.mistral-small-2402-v1:0")]
    [InlineData("mistral.mixtral-8x7b-instruct-v0:1")]
    public async Task ChatStreamingReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello, I'm Alexa, how are you?");
        chatHistory.AddAssistantMessage("I'm doing well, thanks for asking.");
        chatHistory.AddUserMessage("What is 2 + 2?");

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId).Build();
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var response = chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
        string output = "";
        await foreach (var message in response)
        {
            output += message.Content;
            Assert.NotNull(message.InnerContent);
        }
        chatHistory.AddAssistantMessage(output);

        // Assert
        Assert.NotNull(output);
        Assert.Equal(4, chatHistory.Count);
        Assert.Equal(AuthorRole.Assistant, chatHistory[3].Role);
        Assert.False(string.IsNullOrEmpty(output));
    }

    private sealed class TestPlugin
    {
        [KernelFunction()]
        [Description("Given a document title, look up the corresponding document ID for it.")]
        [return: Description("The identified document if found, or an empty string if not.")]
        public string FindDocumentIdForTitle(
            [Description("The title to retrieve a corresponding ID for")]
            string title
        )
        {
            return $"{title}-{Guid.NewGuid()}";
        }
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("anthropic.claude-3-5-sonnet-20241022-v2:0")]
    [InlineData("anthropic.claude-3-5-sonnet-20240620-v1:0")]
    public async Task ChatWithClaudeUsingToolsReturnsValidResponseAsync(string modelId)
    {
        // This test is only for Claude 3.5
        Assert.Contains("anthropic.claude-3", modelId);

        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("I'm looking for a document titled \"Green Eggs and Ham\". I need to get it's ID so that I can submit it to the library for retrieval. Can you get me it's ID? I've provided a tool that you can use to look up the document ID.");

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId).Build();
        kernel.ImportPluginFromObject(new TestPlugin(), "TestPlugin");
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var executionSettings = AmazonClaudeExecutionSettings.FromExecutionSettings(null);
        executionSettings.FunctionChoiceBehavior = FunctionChoiceBehavior.Required();

        // Act
        var responses = await chatCompletionService.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel).ConfigureAwait(true);
        Assert.Equal(3, responses.Count);
    }
}
