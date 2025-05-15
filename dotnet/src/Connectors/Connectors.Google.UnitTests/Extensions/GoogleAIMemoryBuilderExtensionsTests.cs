// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="GoogleAIMemoryBuilderExtensions"/> class.
/// </summary>
[Obsolete("Temporary for Obsolete MemoryBuilder extensions tests.")]
public sealed class GoogleAIMemoryBuilderExtensionsTests
{
    private readonly Mock<IMemoryStore> _mockMemoryStore = new();

    [Fact]
    public void ShouldBuildMemoryWithGoogleAIEmbeddingGenerator()
    {
        // Arrange
        var builder = new MemoryBuilder();

        // Act
        var memory = builder
            .WithGoogleAITextEmbeddingGeneration("fake-model", "fake-apikey")
            .WithMemoryStore(this._mockMemoryStore.Object)
            .Build();

        // Assert
        Assert.NotNull(memory);
    }
}
