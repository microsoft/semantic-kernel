// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Amazon.UnitTests;

/// <summary>
/// Unit tests for Bedrock Text Embedding Generation Service.
/// </summary>
public sealed class BedrockTextEmbeddingGenerationServiceTests
{
    /// <summary>
    /// Checks that modelID is added to the list of service attributes when service is registered.
    /// </summary>
    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        string modelId = "amazon.titan-embed-text-v2:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var kernel = Kernel.CreateBuilder().AddBedrockTextEmbeddingGenerationService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Assert
        Assert.Equal(modelId, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    /// <summary>
    /// Checks that an invalid model ID cannot create a new service.
    /// </summary>
    [Fact]
    public void ShouldThrowExceptionForInvalidModelId()
    {
        // Arrange
        string invalidModelId = "invalid.invalid";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();

        // Act
        var kernel = Kernel.CreateBuilder().AddBedrockTextEmbeddingGenerationService(invalidModelId, mockBedrockApi.Object).Build();

        // Assert
        Assert.Throws<KernelException>(() =>
            kernel.GetRequiredService<ITextEmbeddingGenerationService>());
    }

    /// <summary>
    /// Checks that an empty model ID cannot create a new service.
    /// </summary>
    [Fact]
    public void ShouldThrowExceptionForEmptyModelId()
    {
        // Arrange
        string emptyModelId = string.Empty;
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();

        // Act
        var kernel = Kernel.CreateBuilder().AddBedrockTextEmbeddingGenerationService(emptyModelId, mockBedrockApi.Object).Build();

        // Assert
        Assert.Throws<KernelException>(() =>
            kernel.GetRequiredService<ITextEmbeddingGenerationService>());
    }
}
