// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="VertexAIMemoryBuilderExtensions"/> class.
/// </summary>
public sealed class VertexAIMemoryBuilderExtensionsTests
{
    private readonly Mock<IMemoryStore> _mockMemoryStore = new();

    [Fact]
    public void ShouldBuildMemoryWithVertexAIEmbeddingGeneratorBearerAsString()
    {
        // Arrange
        var builder = new MemoryBuilder();

        // Act
        var memory = builder
            .WithVertexAITextEmbeddingGeneration("fake-model", "fake-bearer-key", "fake-location", "fake-project")
            .WithMemoryStore(this._mockMemoryStore.Object)
            .Build();

        // Assert
        Assert.NotNull(memory);
    }

    [Fact]
    public void ShouldBuildMemoryWithVertexAIEmbeddingGeneratorBearerAsFunc()
    {
        // Arrange
        var builder = new MemoryBuilder();

        // Act
        var memory = builder
            .WithVertexAITextEmbeddingGeneration("fake-model", () => "fake-bearer-key", "fake-location", "fake-project")
            .WithMemoryStore(this._mockMemoryStore.Object)
            .Build();

        // Assert
        Assert.NotNull(memory);
    }
}
