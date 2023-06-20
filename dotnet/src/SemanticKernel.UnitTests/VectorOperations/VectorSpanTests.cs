// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI.Embeddings;
using Xunit;

namespace SemanticKernel.UnitTests.VectorOperations;

public class VectorSpanTests
{
    private readonly float[] _floatV1 = new float[] { 1.0F, 2.0F, -4.0F, 10.0F };
    private readonly float[] _floatV2 = new float[] { 3.0F, -7.0F, 1.0F, 6.0F };

    private readonly double[] _doubleV1 = new double[] { 1.0, 2.0, -4.0, 10.0 };
    private readonly double[] _doubleV2 = new double[] { 3.0, -7.0, 1.0, 6.0 };

    [Fact]
    public void ItOnlySupportsFPDataTypes()
    {
        // Assert
        TestTypeUnmanaged<float>(true);
        TestTypeUnmanaged<double>(true);

        TestTypeUnmanaged<bool>(false);
        TestTypeUnmanaged<byte>(false);
        TestTypeUnmanaged<sbyte>(false);
        TestTypeUnmanaged<char>(false);
        TestTypeUnmanaged<decimal>(false);
        TestTypeUnmanaged<int>(false);
        TestTypeUnmanaged<uint>(false);
        TestTypeUnmanaged<nint>(false);
        TestTypeUnmanaged<nuint>(false);
        TestTypeUnmanaged<long>(false);
        TestTypeUnmanaged<ulong>(false);
        TestTypeUnmanaged<short>(false);
        TestTypeUnmanaged<ushort>(false);
        TestType<object>(false);
        TestType<string>(false);

        static void TestType<T>(bool expected)
        {
            if (expected)
            {
                Assert.True(Embedding.IsSupported<T>());
                Assert.True(Embedding.IsSupported(typeof(T)));
                Assert.Contains(typeof(T), Embedding.SupportedTypes);
            }
            else
            {
                Assert.False(Embedding.IsSupported<T>());
                Assert.False(Embedding.IsSupported(typeof(T)));
                Assert.DoesNotContain(typeof(T), Embedding.SupportedTypes);
            }
        }

        static void TestTypeUnmanaged<T>(bool expected) where T : unmanaged
        {
            TestType<T>(expected);
            if (expected)
            {
                _ = new Embedding<T>(Array.Empty<T>());
                _ = new Embedding<T>(Array.Empty<T>(), transferOwnership: true);
                _ = new EmbeddingSpan<T>(Array.Empty<T>());
                _ = new EmbeddingReadOnlySpan<T>(Array.Empty<T>());
            }
            else
            {
                Assert.False(Embedding.IsSupported<T>());
                Assert.False(Embedding.IsSupported(typeof(T)));
                Assert.DoesNotContain(typeof(T), Embedding.SupportedTypes);
                Assert.Throws<NotSupportedException>(() => new Embedding<T>(Array.Empty<T>()));
                Assert.Throws<NotSupportedException>(() => new Embedding<T>(Array.Empty<T>(), transferOwnership: true));
                Assert.Throws<NotSupportedException>(() => new EmbeddingSpan<T>(Array.Empty<T>()));
                Assert.Throws<NotSupportedException>(() => new EmbeddingReadOnlySpan<T>(Array.Empty<T>()));
            }
        }
    }

    [Fact]
    public void ItCanComputeCosineSimilarityFloats()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<float>(this._floatV1);
        var vSpan2 = new EmbeddingSpan<float>(this._floatV2);
        var target = vSpan1.CosineSimilarity(vSpan2);

        // Assert
        Assert.Equal(0.41971841676, target, 5);
    }

    [Fact]
    public void ItCanComputeCosineSimilarityDouble()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<double>(this._doubleV1);
        var vSpan2 = new EmbeddingSpan<double>(this._doubleV2);
        var target = vSpan1.CosineSimilarity(vSpan2);

        // Assert
        Assert.Equal(0.41971841676, target, 5);
    }

    [Fact]
    public void ItThrowsOnCosineSimilarityWithDifferentLengthVectorsFloat()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<float>(this._floatV1);
        var vSpan2 = new EmbeddingSpan<float>(new float[] { -1.0F, 4.0F });

        // Assert
        try
        {
            vSpan1.CosineSimilarity(vSpan2);
            Assert.True(false, "No exception thrown");
        }
        catch (ArgumentException target)
        {
            Assert.IsType<ArgumentException>(target);
        }
    }

    [Fact]
    public void ItThrowsOnCosineSimilarityWithDifferentLengthVectorsDouble()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<double>(this._doubleV1);
        var vSpan2 = new EmbeddingSpan<double>(new double[] { -1.0, 4.0 });

        // Assert
        try
        {
            vSpan1.CosineSimilarity(vSpan2);
            Assert.True(false, "No exception thrown");
        }
        catch (ArgumentException target)
        {
            Assert.IsType<ArgumentException>(target);
        }
    }

    [Fact]
    public void ItCanComputeEuclideanLengthFloat()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<float>(this._floatV1);

        // Act
        var target = vSpan1.EuclideanLength();

        // Assert
        Assert.Equal(11.0, target, 5);
    }

    [Fact]
    public void ItCanComputeEuclideanLengthDouble()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<double>(this._doubleV1);

        // Act
        var target = vSpan1.EuclideanLength();

        // Assert
        Assert.Equal(11.0, target, 5);
    }

    [Fact]
    public void ItCanComputeDotProductFloat()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<float>(this._floatV1);
        var vSpan2 = new EmbeddingSpan<float>(this._floatV2);

        // Act
        var target = vSpan1.Dot(vSpan2);

        // Assert
        Assert.Equal(45.0, target, 5);
    }

    [Fact]
    public void ItCanComputeDotProductDouble()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<double>(this._doubleV1);
        var vSpan2 = new EmbeddingSpan<double>(this._doubleV2);

        // Act
        var target = vSpan1.Dot(vSpan2);

        // Assert
        Assert.Equal(45.0, target, 5);
    }

    [Fact]
    public void ItThrowsOnDotProductWithDifferentLengthVectorsFP()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<float>(this._floatV1);
        var vSpan2 = new EmbeddingSpan<float>(new float[] { -1.0F, 4.0F });

        // Assert
        try
        {
            vSpan1.Dot(vSpan2);
            Assert.True(false, "No exception thrown");
        }
        catch (ArgumentException target)
        {
            Assert.IsType<ArgumentException>(target);
        }
    }

    [Fact]
    public void ItThrowsOnDotProductWithDifferentLengthVectorsDouble()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<double>(this._doubleV1);
        var vSpan2 = new EmbeddingSpan<double>(new double[] { -1.0, 4.0 });

        // Assert
        try
        {
            vSpan1.Dot(vSpan2);
            Assert.True(false, "No exception thrown");
        }
        catch (ArgumentException target)
        {
            Assert.IsType<ArgumentException>(target);
        }
    }

    [Fact]
    public void ItCanBeNormalizedFloat()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<float>(this._floatV1);

        // Act
        var target = vSpan1.Normalize();
        var expected = new EmbeddingSpan<float>(new float[] { 0.09090909F, 0.18181819F, -0.3636364F, 0.90909094F });

        // Assert
        Assert.True(target.IsNormalized);
        Assert.Equal(vSpan1.Span.Length, target.ReadOnlySpan.Length);
        for (int i = 0; i < vSpan1.Span.Length; i++)
        {
            Assert.Equal(expected.Span[i], target.ReadOnlySpan[i], .00001F);
        }
    }

    [Fact]
    public void ItCanBeNormalizedDouble()
    {
        // Arrange
        var vSpan1 = new EmbeddingSpan<double>(this._doubleV1);

        // Act
        var target = vSpan1.Normalize();
        var expected = new EmbeddingSpan<double>(new double[] { 0.09090909, 0.18181819, -0.3636364, 0.90909094 });

        // Assert
        Assert.True(target.IsNormalized);
        Assert.Equal(vSpan1.Span.Length, target.ReadOnlySpan.Length);
        for (int i = 0; i < vSpan1.Span.Length; i++)
        {
            Assert.Equal(expected.Span[i], target.ReadOnlySpan[i], .00001);
        }
    }
}
