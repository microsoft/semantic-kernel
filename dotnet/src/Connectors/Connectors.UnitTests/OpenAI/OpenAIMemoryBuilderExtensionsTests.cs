// Copyright (c) Microsoft. All rights reserved.

using Azure.Core;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests for <see cref="OpenAIMemoryBuilderExtensions"/> class.
/// </summary>
public sealed class OpenAIMemoryBuilderExtensionsTests
{
    private readonly Mock<IMemoryStore> _mockMemoryStore = new();

    [Fact]
    public void AzureOpenAITextEmbeddingGenerationWithApiKeyWorksCorrectly()
    {
        // Arrange
        var builder = new MemoryBuilder();

        // Act
        var memory = builder
            .WithAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", "api-key", "model-id")
            .WithMemoryStore(this._mockMemoryStore.Object)
            .Build();

        // Assert
        Assert.NotNull(memory);
    }

    [Fact]
    public void AzureOpenAITextEmbeddingGenerationWithTokenCredentialWorksCorrectly()
    {
        // Arrange
        var builder = new MemoryBuilder();
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());

        // Act
        var memory = builder
            .WithAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", credentials, "model-id")
            .WithMemoryStore(this._mockMemoryStore.Object)
            .Build();

        // Assert
        Assert.NotNull(memory);
    }

    [Fact]
    public void OpenAITextEmbeddingGenerationWithApiKeyWorksCorrectly()
    {
        // Arrange
        var builder = new MemoryBuilder();

        // Act
        var memory = builder
            .WithOpenAITextEmbeddingGeneration("model-id", "api-key", "organization-id")
            .WithMemoryStore(this._mockMemoryStore.Object)
            .Build();

        // Assert
        Assert.NotNull(memory);
    }
}
