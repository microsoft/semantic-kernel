// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Amazon;

public class BedrockChatClientTests
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
        var kernel = Kernel.CreateBuilder().AddBedrockChatClient(modelId).Build();

        // Act
        var message = await kernel.InvokePromptAsync<ChatMessage>("Hello, I'm Alexa, how are you?").ConfigureAwait(true);

        // Assert
        Assert.NotNull(message);
        Assert.Equal(ChatRole.Assistant, message.Role);
        Assert.NotNull(message.Text);
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
        var kernel = Kernel.CreateBuilder().AddBedrockChatClient(modelId).Build();

        // Act
        var response = kernel.InvokePromptStreamingAsync<ChatResponseUpdate>("Hello, I'm Alexa, how are you?").ConfigureAwait(true);
        string output = "";
        await foreach (var message in response)
        {
            output += message.Text;
            Assert.NotNull(message.RawRepresentation);
        }

        // Assert
        Assert.NotNull(output);
        Assert.False(string.IsNullOrEmpty(output));
    }
}
