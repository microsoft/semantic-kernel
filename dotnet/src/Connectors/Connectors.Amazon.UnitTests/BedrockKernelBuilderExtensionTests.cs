// Copyright (c) Microsoft. All rights reserved.

using Connectors.Amazon.Extensions;
using Connectors.Amazon.Services;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Services;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace Connectors.Amazon.UnitTests;

/// <summary>
/// Kernel Builder Extension Tests for Bedrock.
/// </summary>
public class BedrockKernelBuilderExtensionTests
{
    /// <summary>
    /// Checks that AddBedrockTextGenerationService builds a proper kernel.
    /// </summary>
    [Fact]
    public void AddBedrockTextGenerationCreatesService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        builder.AddBedrockTextGenerationService("amazon.titan-text-premier-v1:0");

        // Act
        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        // Assert
        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<BedrockTextGenerationService>(service);
    }
    /// <summary>
    /// Checks that AddBedrockChatCompletionService builds a proper kernel.
    /// </summary>
    [Fact]
    public void AddBedrockChatCompletionCreatesService()
    {
        // Arrange
        var builder = Kernel.CreateBuilder();
        builder.AddBedrockChatCompletionService("amazon.titan-text-premier-v1:0");

        // Act
        var kernel = builder.Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Assert
        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<BedrockChatCompletionService>(service);
    }
}
