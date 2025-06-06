// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
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
        var messages = await chatCompletionService.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
        string output = "";
        foreach (var message in messages)
        {
            output += message.Content;
            Assert.NotNull(message.InnerContent);
        }
        chatHistory.AddAssistantMessage(output);

        // Assert
        Assert.NotNull(output);
        Assert.True(messages.Count > 0);
        Assert.Equal(4, chatHistory.Count);

        var assistantMessage = messages[0];
        Assert.Equal(AuthorRole.Assistant, assistantMessage.Role);
        var response = Assert.IsType<ConverseResponse>(messages[0].InnerContent);
        Assert.NotNull(assistantMessage.Metadata?["Usage"] as TokenUsage);
        Assert.Equal(response.Usage, assistantMessage.Metadata["Usage"]);
        Assert.NotEqual(0, response.Usage.InputTokens);
        Assert.NotEqual(0, response.Usage.OutputTokens);
        Assert.NotEqual(0, response.Usage.TotalTokens);
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
            if (message.Metadata != null)
            {
                Assert.NotEmpty(message.Metadata);
                Assert.Contains("Usage", message.Metadata.Keys);
                var metadataChunk = Assert.IsType<ConverseStreamMetadataEvent>(message.InnerContent);
                var tokenUsage = Assert.IsType<TokenUsage>(message.Metadata["Usage"]);
                Assert.Same(metadataChunk.Usage, tokenUsage);
                Assert.NotEqual(0, tokenUsage.InputTokens);
                Assert.NotEqual(0, tokenUsage.OutputTokens);
                Assert.NotEqual(0, tokenUsage.TotalTokens);
            }
        }
        chatHistory.AddAssistantMessage(output);

        // Assert
        Assert.NotNull(output);
        Assert.Equal(4, chatHistory.Count);
        Assert.Equal(AuthorRole.Assistant, chatHistory[3].Role);
        Assert.False(string.IsNullOrEmpty(output));
    }
}
