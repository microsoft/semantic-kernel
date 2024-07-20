// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Amazon;
using Connectors.Amazon.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Amazon.Bedrock;

public class BedrockTextGenerationTests
{
    [Theory]
    [InlineData("amazon.titan-text-premier-v1:0")]
    [InlineData("mistral.mistral-7b-instruct-v0:2")]
    [InlineData("ai21.jamba-instruct-v1:0")]
    [InlineData("anthropic.claude-v2:1")]
    [InlineData("cohere.command-text-v14")]
    [InlineData("meta.llama3-8b-instruct-v1:0")]
    [InlineData("cohere.command-r-plus-v1:0")]
    [InlineData("ai21.j2-ultra-v1")]
    public async Task TextGenerationReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        string prompt = "What is 2 + 2?";
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, RegionEndpoint.USEast1).Build();
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();

        // Act
        var response = await textGenerationService.GetTextContentsAsync(prompt).ConfigureAwait(true);

        // Assert
        Assert.NotNull(response);
        Assert.Contains(response, r => r.Text.Contains('4', StringComparison.OrdinalIgnoreCase) || r.Text.Contains("four", StringComparison.OrdinalIgnoreCase));
    }

    [Theory]
    [InlineData("amazon.titan-text-premier-v1:0")]
    [InlineData("anthropic.claude-v2")]
    [InlineData("mistral.mistral-7b-instruct-v0:2")]
    [InlineData("cohere.command-text-v14")]
    [InlineData("cohere.command-r-plus-v1:0")]
    [InlineData("meta.llama3-8b-instruct-v1:0")]
    public async Task TextStreamingReturnsValidResponseAsync(string modelId)
    {
        // Arrange
        string prompt = "What is 2 + 2?";
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, RegionEndpoint.USEast1).Build();
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();

        // Act
        var response = textGenerationService.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true);
        string output = "";
        await foreach (var textContent in response)
        {
            output += textContent.Text;
        }

        // Assert
        Assert.NotNull(output);
        Assert.True(output.Contains('4', StringComparison.OrdinalIgnoreCase) || output.Contains("four", StringComparison.OrdinalIgnoreCase));
    }
}
