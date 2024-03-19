// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

/// <summary>
/// Unit tests for <see cref="MemoryBuilder"/> class.
/// </summary>
public sealed class MemoryBuilderTests
{
    [Fact]
    public void ItThrowsExceptionWhenMemoryStoreIsNotProvided()
    {
        // Arrange
        var builder = new MemoryBuilder();

        // Act
        var exception = Assert.Throws<KernelException>(() => builder.Build());

        // Assert
        Assert.Equal("IMemoryStore dependency was not provided. Use WithMemoryStore method.", exception.Message);
    }

    [Fact]
    public void ItThrowsExceptionWhenEmbeddingGenerationIsNotProvided()
    {
        // Arrange
        var builder = new MemoryBuilder()
            .WithMemoryStore(Mock.Of<IMemoryStore>());

        // Act
        var exception = Assert.Throws<KernelException>(() => builder.Build());

        // Assert
        Assert.Equal("ITextEmbeddingGenerationService dependency was not provided. Use WithTextEmbeddingGeneration method.", exception.Message);
    }

    [Fact]
    public void ItInitializesMemoryWhenRequiredDependenciesAreProvided()
    {
        // Arrange
        var builder = new MemoryBuilder()
            .WithMemoryStore(Mock.Of<IMemoryStore>())
            .WithTextEmbeddingGeneration(Mock.Of<ITextEmbeddingGenerationService>());

        // Act
        var memory = builder.Build();

        // Assert
        Assert.NotNull(memory);
    }
}
