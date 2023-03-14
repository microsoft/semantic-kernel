// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
using Xunit;

namespace SemanticKernel.UnitTests.AI.Embeddings;

public class EmbeddingTests
{
    // Vector has length of 3, magnitude of 5
    private readonly float[] _vector = new float[] { 0, 3, -4 };
    private readonly float[] _empty = Array.Empty<float>();

    [Fact]
    public void ItThrowsWithNullVector()
    {
        // Assert
        Assert.Throws<ValidationException>(() => new Embedding<float>(null!));
    }

    [Fact]
    public void ItCreatesEmptyEmbedding()
    {
        // Arrange
        var target = new Embedding<float>(this._empty);

        // Assert
        Assert.Empty(target.Vector);
        Assert.Equal(0, target.Count);
    }

    [Fact]
    public void ItCreatesExpectedEmbedding()
    {
        // Arrange
        var target = new Embedding<float>(this._vector);

        // Act
        // TODO: copy is never used - bug?
        var copy = target;

        // Assert
        Assert.True(target.Vector.SequenceEqual(this._vector));
    }

    [Fact]
    public void ItSerializesEmbedding()
    {
        // Arrange
        var target = new Embedding<float>(this._vector);

        // Act
        string json = JsonSerializer.Serialize(target);
        var copy = JsonSerializer.Deserialize<Embedding<float>>(json);

        // Assert
        Assert.True(copy.Vector.SequenceEqual(this._vector));
    }
}
