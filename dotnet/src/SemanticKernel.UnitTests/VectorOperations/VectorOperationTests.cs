// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;
using Xunit;

namespace SemanticKernel.UnitTests.VectorOperations;

public class VectorOperationTests
{
    private readonly float[] _floatV1 = new float[] { 1.0F, 2.0F, -4.0F, 10.0F };
    private readonly float[] _floatV2 = new float[] { 3.0F, -7.0F, 1.0F, 6.0F };

    private readonly double[] _doubleV1 = new double[] { 1.0, 2.0, -4.0, 10.0 };
    private readonly double[] _doubleV2 = new double[] { 3.0, -7.0, 1.0, 6.0 };

    [Fact]
    public void ItComputesCosineSimilarityFloat()
    {
        // Arrange
        var target = this._floatV1.CosineSimilarity(this._floatV2);

        // Assert
        Assert.Equal(0.41971841676, target, 5);
    }

    [Fact]
    public void ItComputesCosineSimilarityDouble()
    {
        // Arrange
        var target = this._doubleV1.CosineSimilarity(this._doubleV2);

        // Assert
        Assert.Equal(0.41971841676, target, 5);
    }

    [Fact]
    public void ItThrowsOnCosineSimilarityWithDifferentLengthVectorsFP()
    {
        // Arrange
        var shortVector = new float[] { -1.0F, 4.0F };

        // Assert
        Assert.Throws<ArgumentException>(() => shortVector.CosineSimilarity(this._floatV2));
    }

    [Fact]
    public void ItThrowsOnCosineSimilarityWithDifferentLengthVectorsDouble()
    {
        // Arrange
        var shortVector = new double[] { -1.0, 4.0 };

        // Assert
        Assert.Throws<ArgumentException>(() => shortVector.CosineSimilarity(this._doubleV2));
    }

    [Fact]
    public void ItComputesEuclideanLengthFloat()
    {
        // Arrange
        var target = this._floatV1.EuclideanLength();

        // Assert
        Assert.Equal(11.0, target, 5);
    }

    [Fact]
    public void ItComputesEuclideanLengthDouble()
    {
        // Arrange
        var target = this._doubleV1.EuclideanLength();

        // Assert
        Assert.Equal(11.0, target, 5);
    }

    [Theory]
    [InlineData(0, 0)]
    [InlineData(1, 3.0)]
    [InlineData(2, -11.0)]
    [InlineData(3, -15.0)]
    [InlineData(4, 45.0)]
    public void ItComputesDotProductFloat(int length, double expectedResult)
    {
        // Arrange
        var target = this._floatV1.AsSpan(0, length).DotProduct(this._floatV2.AsSpan(0, length));

        // Assert
        Assert.Equal(expectedResult, target, 5);
    }

    [Theory]
    [InlineData(0, 0)]
    [InlineData(1, 3.0)]
    [InlineData(2, -11.0)]
    [InlineData(3, -15.0)]
    [InlineData(4, 45.0)]
    public void ItComputesDotProductDouble(int length, double expectedResult)
    {
        // Arrange
        var target = this._doubleV1.AsSpan(0, length).DotProduct(this._doubleV2.AsSpan(0, length));

        // Assert
        Assert.Equal(expectedResult, target, 5);
    }

    [Fact]
    public void ItNormalizesInPlaceFloat()
    {
        // Arrange
        var target = this._floatV1;
        target.NormalizeInPlace();
        var expected = new float[] { 0.09090909F, 0.18181819F, -0.3636364F, 0.90909094F };

        // Assert
        Assert.Equal(expected.Length, target.Length);
        for (int i = 0; i < expected.Length; i++)
        {
            Assert.Equal(expected[i], target[i], .00001F);
        }
    }

    [Fact]
    public void ItNormalizesInPlaceDouble()
    {
        // Arrange
        var target = this._doubleV1;
        target.NormalizeInPlace();
        var expected = new double[] { 0.09090909, 0.18181819, -0.3636364, 0.90909094 };

        // Assert
        Assert.Equal(expected.Length, target.Length);
        for (int i = 0; i < expected.Length; i++)
        {
            Assert.Equal(expected[i], target[i], .00001);
        }
    }

    [Fact]
    public void ItMultipliesInPlaceFloat()
    {
        // Arrange
        var target = this._floatV1;
        target.MultiplyByInPlace(2);
        var expected = new float[] { 2.0F, 4.0F, -8.0F, 20.0F };

        // Assert
        Assert.Equal(expected.Length, target.Length);
        for (int i = 0; i < expected.Length; i++)
        {
            Assert.Equal(expected[i], target[i], .00001F);
        }
    }

    [Fact]
    public void ItMultipliesInPlaceDouble()
    {
        // Arrange
        var target = this._doubleV1;
        target.MultiplyByInPlace(2);
        var expected = new double[] { 2.0, 4.0, -8.0, 20.0 };

        // Assert
        Assert.Equal(expected.Length, target.Length);
        for (int i = 0; i < expected.Length; i++)
        {
            Assert.Equal(expected[i], target[i], .00001);
        }
    }

    [Fact]
    public void ItDividesInPlaceFloat()
    {
        // Arrange
        var target = this._floatV1;
        target.DivideByInPlace(2);
        var expected = new float[] { 0.5F, 1.0F, -2.0F, 5.0F };

        // Assert
        Assert.Equal(expected.Length, target.Length);
        for (int i = 0; i < expected.Length; i++)
        {
            Assert.Equal(expected[i], target[i], .00001F);
        }
    }

    [Fact]
    public void ItDividesInPlaceDouble()
    {
        // Arrange
        var target = this._doubleV1;
        target.DivideByInPlace(2);
        var expected = new double[] { 0.5, 1.0, -2.0, 5.0 };

        // Assert
        Assert.Equal(expected.Length, target.Length);
        for (int i = 0; i < expected.Length; i++)
        {
            Assert.Equal(expected[i], target[i], .00001);
        }
    }

    [Fact]
    public void ItProducesExpectedCosineSimilarityResultsFloat()
    {
        // Arrange
        var vectorList = new List<float[]>();
        var comparisonVector = new float[] { 1.0F, 1.0F, 1.0F, 1.0F };
        vectorList.Add(new float[] { 1.0F, 1.0F, 1.0F, 1.0F }); // identical
        vectorList.Add(new float[] { 1.0F, 1.0F, 1.0F, 2.0F });
        vectorList.Add(new float[] { 1.0F, 1.0F, -1.0F, -1.0F });
        vectorList.Add(new float[] { -1.0F, -1.0F, -1.0F, -1.0F }); // least similar

        // Act
        var target = vectorList.Select(x => x.CosineSimilarity(comparisonVector)).ToArray();

        // Assert
        Assert.Equal(1.0, target[0]); // identical vectors results in similarity of 1
        Assert.True(target[0] > target[1]);
        Assert.True(target[1] > target[2]);
        Assert.True(target[2] > target[3]);
        Assert.Equal(-1.0, target[3]); // opposing vectors results in similarity of -1
    }

    [Fact]
    public void ItProducesExpectedCosineSimilarityResultsDouble()
    {
        // Arrange
        var vectorList = new List<double[]>();
        var comparisonVector = new double[] { 1.0, 1.0, 1.0, 1.0 };
        vectorList.Add(new double[] { 1.0, 1.0, 1.0, 1.0 }); // identical
        vectorList.Add(new double[] { 1.0, 1.0, 1.0, 2.0 });
        vectorList.Add(new double[] { 1.0, 1.0, -1.0, -1.0 });
        vectorList.Add(new double[] { -1.0, -1.0, -1.0, -1.0 }); // least similar

        // Act
        var target = vectorList.Select(x => x.CosineSimilarity(comparisonVector)).ToArray();

        // Assert
        Assert.Equal(1.0, target[0]); // identical vectors results in similarity of 1
        Assert.True(target[0] > target[1]);
        Assert.True(target[1] > target[2]);
        Assert.True(target[2] > target[3]);
        Assert.Equal(-1.0, target[3]); // opposing vectors results in similarity of -1
    }
}
