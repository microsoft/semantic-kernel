// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.Runtime;
using Microsoft.Extensions.DependencyInjection;
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

    /// <summary>
    /// Checks that an invalid BedrockRuntime object will throw an exception.
    /// </summary>
    [Fact]
    public async Task ShouldThrowExceptionForNullBedrockRuntimeWhenNotConfiguredAsync()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v2:0";
        List<string> prompts = new() { "King", "Queen", "Prince" };
        IAmazonBedrockRuntime? nullBedrockRuntime = null;
        bool notConfigured = false;

        try
        {
            var runtime = new ServiceCollection()
                .TryAddAWSService<IAmazonBedrockRuntime>()
                .BuildServiceProvider()
                .GetService<IAmazonBedrockRuntime>();
        }
        catch (AmazonClientException)
        {
            // If cannot grab the runtime from the container then we are not configured
            notConfigured = true;
        }

        // Act
        if (notConfigured)
        {
            // If No RegionEndpoint or ServiceURL is configured, the runtime will throw an exception
            await Assert.ThrowsAnyAsync<Exception>(async () =>
            {
                var kernel = Kernel.CreateBuilder().AddBedrockTextEmbeddingGenerationService(modelId, nullBedrockRuntime).Build();
                var service = kernel.GetRequiredService<ITextEmbeddingGenerationService>();
                await service.GenerateEmbeddingsAsync(prompts).ConfigureAwait(true);
            }).ConfigureAwait(true);
        }
    }
}
