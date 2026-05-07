// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Amazon;

public class BedrockTextGenerationTests
{
    [Theory(Skip = "For manual verification only")]
    [InlineData("cohere.command-text-v14")]
    [InlineData("cohere.command-light-text-v14")]
    [InlineData("cohere.command-r-v1:0")]
    [InlineData("cohere.command-r-plus-v1:0")]
    [InlineData("ai21.jamba-instruct-v1:0")]
    [InlineData("meta.llama3-70b-instruct-v1:0")]
    [InlineData("meta.llama3-8b-instruct-v1:0")]
    [InlineData("mistral.mistral-7b-instruct-v0:2")]
    [InlineData("mistral.mistral-large-2402-v1:0")]
    [InlineData("mistral.mistral-small-2402-v1:0")]
    [InlineData("mistral.mixtral-8x7b-instruct-v0:1")]
    [InlineData("amazon.titan-text-premier-v1:0")]
    [InlineData("amazon.titan-text-lite-v1")]
    [InlineData("amazon.titan-text-express-v1")]
    public async Task TextGenerationReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        string prompt = "What is 2 + 2?";
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId).Build();
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();

        // Act
        var response = await textGenerationService.GetTextContentsAsync(prompt).ConfigureAwait(true);
        string output = "";
        foreach (var text in response)
        {
            output += text;
            Assert.NotNull(text.InnerContent);
        }

        // Assert
        Assert.NotNull(response);
        Assert.True(response.Count > 0);
        Assert.False(string.IsNullOrEmpty(output));
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("anthropic.claude-v2")]
    [InlineData("anthropic.claude-v2:1")]
    [InlineData("anthropic.claude-instant-v1")]
    public async Task AnthropicTextGenerationReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        string prompt = """
                        Human: What is 2 + 2?
                        Assistant: 
                        """;
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId).Build();
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();

        // Act
        var response = await textGenerationService.GetTextContentsAsync(prompt).ConfigureAwait(true);
        string output = "";
        foreach (var text in response)
        {
            output += text;
            Assert.NotNull(text.InnerContent);
        }

        // Assert
        Assert.NotNull(response);
        Assert.True(response.Count > 0);
        Assert.False(string.IsNullOrEmpty(output));
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("ai21.jamba-instruct-v1:0")]
    [InlineData("cohere.command-text-v14")]
    [InlineData("cohere.command-light-text-v14")]
    [InlineData("cohere.command-r-v1:0")]
    [InlineData("cohere.command-r-plus-v1:0")]
    [InlineData("meta.llama3-70b-instruct-v1:0")]
    [InlineData("meta.llama3-8b-instruct-v1:0")]
    [InlineData("mistral.mistral-7b-instruct-v0:2")]
    [InlineData("mistral.mistral-large-2402-v1:0")]
    [InlineData("mistral.mistral-small-2402-v1:0")]
    [InlineData("mistral.mixtral-8x7b-instruct-v0:1")]
    [InlineData("amazon.titan-text-premier-v1:0")]
    [InlineData("amazon.titan-text-lite-v1")]
    [InlineData("amazon.titan-text-express-v1")]
    public async Task TextStreamingReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        string prompt = "What is 2 + 2?";
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId).Build();
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();

        // Act
        var response = textGenerationService.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true);
        string output = "";
        await foreach (var textContent in response)
        {
            output += textContent.Text;
            Assert.NotNull(textContent.InnerContent);
        }

        // Assert
        Assert.NotNull(output);
        Assert.False(string.IsNullOrEmpty(output));
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("anthropic.claude-v2")]
    [InlineData("anthropic.claude-v2:1")]
    [InlineData("anthropic.claude-instant-v1")]
    public async Task AnthropicTextStreamingReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        string prompt = """
                        Human: What is 2 + 2?
                        Assistant: 
                        """;
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId).Build();
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();

        // Act
        var response = textGenerationService.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true);
        string output = "";
        await foreach (var textContent in response)
        {
            output += textContent.Text;
            Assert.NotNull(textContent.InnerContent);
        }

        // Assert
        Assert.NotNull(output);
        Assert.False(string.IsNullOrEmpty(output));
    }
}
