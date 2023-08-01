// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text.Json;
using Microsoft.SemanticKernel.AI.Embeddings;
using Xunit;

namespace SemanticKernel.Plugins.Memory.UnitTests.Embeddings;

public class EmbeddingTests
{
    // Vector has length of 3, magnitude of 5
    private readonly float[] _vector = new float[] { 0, 3, -4 };
    private readonly float[] _empty = Array.Empty<float>();

    [Fact]
    public void ItTreatsDefaultEmbeddingAsEmpty()
    {
        // Arrange
        Embedding<float> target = default;

        // Assert
        Assert.True(target.IsEmpty);
        Assert.Equal(0, target.Count);
        Assert.Empty(target.Vector);
        Assert.Same(Array.Empty<float>(), target.Vector);
        Assert.Same(Array.Empty<float>(), (float[])target);
        Assert.True(target.AsReadOnlySpan().IsEmpty);
        Assert.True(((ReadOnlySpan<float>)target).IsEmpty);
        Assert.True(target.Equals(Embedding<float>.Empty));
        Assert.True(target.Equals(new Embedding<float>()));
        Assert.True(target == Embedding<float>.Empty);
        Assert.True(target == new Embedding<float>());
        Assert.False(target != Embedding<float>.Empty);
        Assert.Equal(0, target.GetHashCode());
    }

    [Fact]
    public void ItThrowsFromCtorWithUnsupportedType()
    {
        // Assert
        Assert.Throws<NotSupportedException>(() => new Embedding<int>(new int[] { 1, 2, 3 }));
        Assert.Throws<NotSupportedException>(() => new Embedding<int>(Array.Empty<int>()));
    }

    [Fact]
    public void ItThrowsFromEmptyWithUnsupportedType()
    {
        // Assert
        Assert.Throws<NotSupportedException>(() => Embedding<int>.Empty);
    }

    [Fact]
    public void ItAllowsUnsupportedTypesOnEachOperation()
    {
        // Arrange
        Embedding<int> target = default;

        // Act
        Assert.True(target.IsEmpty);
        Assert.Equal(0, target.Count);
    }

    [Fact]
    public void ItThrowsWithNullVector()
    {
        // Assert
        Assert.Throws<ArgumentNullException>("vector", () => new Embedding<float>(null!));
    }

    [Fact]
    public void ItCreatesEmptyEmbedding()
    {
        // Arrange
        var target = new Embedding<float>(this._empty);

        // Assert
        Assert.Empty(target.Vector);
        Assert.Equal(0, target.Count);
        Assert.False(Embedding.IsSupported<int>());
    }

    [Fact]
    public void ItCreatesExpectedEmbedding()
    {
        // Arrange
        var target = new Embedding<float>(this._vector);

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

    [Fact]
    public void ItDoesntCopyVectorWhenCastingToSpan()
    {
        // Arrange
        var target = new Embedding<float>(this._vector);

        // Act
        ReadOnlySpan<float> span1 = target.AsReadOnlySpan();
        ReadOnlySpan<float> span2 = (ReadOnlySpan<float>)target;

        // Assert
        Assert.False(Unsafe.AreSame(ref MemoryMarshal.GetReference(span1), ref MemoryMarshal.GetArrayDataReference(this._vector)));
        Assert.True(Unsafe.AreSame(ref MemoryMarshal.GetReference(span1), ref MemoryMarshal.GetReference(span2)));
    }

    [Fact]
    public void ItTransfersOwnershipWhenRequested()
    {
        // Assert
        Assert.False(ReferenceEquals(this._vector, new Embedding<float>(this._vector).Vector));
        Assert.False(ReferenceEquals(this._vector, new Embedding<float>(this._vector, transferOwnership: false).Vector));
        Assert.True(ReferenceEquals(this._vector, new Embedding<float>(this._vector, transferOwnership: true).Vector));
    }
}
