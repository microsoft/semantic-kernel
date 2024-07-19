// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Amazon;
using Connectors.Amazon.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Amazon.Bedrock;

public class BedrockTextGenerationTests
{
    [Fact]
    public async Task TextGenerationReturnsValidResponseAsync()
    {
        // Arrange
        string prompt = "What is 2 + 2?";
        string modelId = "amazon.titan-text-premier-v1:0";
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, RegionEndpoint.USEast1).Build();
        var chatCompletionService = kernel.GetRequiredService<ITextGenerationService>();

        // Act
        var response = await chatCompletionService.GetTextContentsAsync(prompt).ConfigureAwait(true);

        // Assert
        Assert.NotNull(response);
        Assert.Contains("4", response[0].Text, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task TextStreamingReturnsValidResponseAsync()
    {
        // Arrange
        string prompt = "What is 2 + 2?";
        string modelId = "amazon.titan-text-premier-v1:0";
        var kernel = Kernel.CreateBuilder().AddBedrockTextGenerationService(modelId, RegionEndpoint.USEast1).Build();
        var chatCompletionService = kernel.GetRequiredService<ITextGenerationService>();

        // Act
        var response = chatCompletionService.GetStreamingTextContentsAsync(prompt).ConfigureAwait(true);
        string output = "";
        await foreach (var textContent in response)
        {
            output += textContent.Text;
        }

        // Assert
        Assert.NotNull(output);
        Assert.Contains("4", output, StringComparison.OrdinalIgnoreCase);
    }
}
