// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisCollectionSearchMapping"/> class.
/// </summary>
public class RedisCollectionSearchMappingTests
{
    [Fact]
    public void ValidateVectorAndConvertToBytesConvertsFloatVector()
    {
        // Arrange.
        var floatVector = new ReadOnlyMemory<float>(new float[] { 1.0f, 2.0f, 3.0f });

        // Act.
        var byteArray = RedisCollectionSearchMapping.ValidateVectorAndConvertToBytes(floatVector, "Test");

        // Assert.
        Assert.NotNull(byteArray);
        Assert.Equal(12, byteArray.Length);
        Assert.Equal(new byte[12] { 0, 0, 128, 63, 0, 0, 0, 64, 0, 0, 64, 64 }, byteArray);
    }

    [Fact]
    public void ValidateVectorAndConvertToBytesConvertsDoubleVector()
    {
        // Arrange.
        var doubleVector = new ReadOnlyMemory<double>(new double[] { 1.0, 2.0, 3.0 });

        // Act.
        var byteArray = RedisCollectionSearchMapping.ValidateVectorAndConvertToBytes(doubleVector, "Test");

        // Assert.
        Assert.NotNull(byteArray);
        Assert.Equal(24, byteArray.Length);
        Assert.Equal(new byte[24] { 0, 0, 0, 0, 0, 0, 240, 63, 0, 0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0, 0, 8, 64 }, byteArray);
    }

    [Fact]
    public void ValidateVectorAndConvertToBytesThrowsForUnsupportedType()
    {
        // Arrange.
        var unsupportedVector = new ReadOnlyMemory<int>(new int[] { 1, 2, 3 });

        // Act & Assert.
        var exception = Assert.Throws<NotSupportedException>(() =>
        {
            var byteArray = RedisCollectionSearchMapping.ValidateVectorAndConvertToBytes(unsupportedVector, "Test");
        });
        Assert.Equal("The provided vector type System.ReadOnlyMemory`1[[System.Int32, System.Private.CoreLib, Version=10.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]] is not supported by the Redis Test connector.", exception.Message);
    }

    [Fact]
    public void BuildQueryBuildsRedisQueryWithDefaults()
    {
        // Arrange.
        var floatVector = new ReadOnlyMemory<float>(new float[] { 1.0f, 2.0f, 3.0f });
        var byteArray = MemoryMarshal.AsBytes(floatVector.Span).ToArray();
        var model = BuildModel(
        [
            new VectorStoreKeyProperty("Key", typeof(string)),
            new VectorStoreVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 10)
        ]);

        // Act.
        var query = RedisCollectionSearchMapping.BuildQuery(byteArray, top: 3, new VectorSearchOptions<DummyType>(), model, model.VectorProperty, null);

        // Assert.
        Assert.NotNull(query);
        Assert.Equal("*=>[KNN 3 @Vector $embedding AS vector_score]", query.QueryString);
        Assert.Equal("vector_score", query.SortBy);
        Assert.True(query.WithScores);
        Assert.Equal(2, query.dialect);
    }

    [Fact]
    public void BuildQueryBuildsRedisQueryWithCustomVectorName()
    {
        // Arrange.
        var floatVector = new ReadOnlyMemory<float>(new float[] { 1.0f, 2.0f, 3.0f });
        var byteArray = MemoryMarshal.AsBytes(floatVector.Span).ToArray();
        var vectorSearchOptions = new VectorSearchOptions<DummyType> { Skip = 3 };
        var model = BuildModel(
        [
            new VectorStoreKeyProperty("Key", typeof(string)),
            new VectorStoreVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 10) { StorageName = "storage_Vector" }
        ]);
        var selectFields = new string[] { "storage_Field1", "storage_Field2" };

        // Act.
        var query = RedisCollectionSearchMapping.BuildQuery(byteArray, top: 5, vectorSearchOptions, model, model.VectorProperty, selectFields);

        // Assert.
        Assert.NotNull(query);
        Assert.Equal("*=>[KNN 8 @storage_Vector $embedding AS vector_score]", query.QueryString);
    }

    [Fact]
    public void ResolveDistanceFunctionReturnsCosineSimilarityIfNoDistanceFunctionSpecified()
    {
        var property = new VectorPropertyModel("Prop", typeof(ReadOnlyMemory<float>));

        // Act.
        var resolvedDistanceFunction = RedisCollectionSearchMapping.ResolveDistanceFunction(property);

        // Assert.
        Assert.Equal(DistanceFunction.CosineSimilarity, resolvedDistanceFunction);
    }

    [Fact]
    public void ResolveDistanceFunctionReturnsDistanceFunctionFromProvidedProperty()
    {
        var property = new VectorPropertyModel("Prop", typeof(ReadOnlyMemory<float>)) { DistanceFunction = DistanceFunction.DotProductSimilarity };

        // Act.
        var resolvedDistanceFunction = RedisCollectionSearchMapping.ResolveDistanceFunction(property);

        // Assert.
        Assert.Equal(DistanceFunction.DotProductSimilarity, resolvedDistanceFunction);
    }

    [Fact]
    public void GetOutputScoreFromRedisScoreConvertsCosineDistanceToSimilarity()
    {
        // Act & Assert.
        Assert.Equal(-1, RedisCollectionSearchMapping.GetOutputScoreFromRedisScore(2, DistanceFunction.CosineSimilarity));
        Assert.Equal(0, RedisCollectionSearchMapping.GetOutputScoreFromRedisScore(1, DistanceFunction.CosineSimilarity));
        Assert.Equal(1, RedisCollectionSearchMapping.GetOutputScoreFromRedisScore(0, DistanceFunction.CosineSimilarity));
    }

    [Theory]
    [InlineData(DistanceFunction.CosineDistance, 2)]
    [InlineData(DistanceFunction.DotProductSimilarity, 2)]
    [InlineData(DistanceFunction.EuclideanSquaredDistance, 2)]
    public void GetOutputScoreFromRedisScoreLeavesNonConsineSimilarityUntouched(string distanceFunction, float score)
    {
        // Act & Assert.
        Assert.Equal(score, RedisCollectionSearchMapping.GetOutputScoreFromRedisScore(score, distanceFunction));
    }

#pragma warning disable CA1812 // An internal class that is apparently never instantiated. If so, remove the code from the assembly.
    private sealed class DummyType;
#pragma warning restore CA1812

    private static CollectionModel BuildModel(List<VectorStoreProperty> properties)
        => new RedisModelBuilder(RedisHashSetCollection<string, DummyType>.ModelBuildingOptions)
            .BuildDynamic(new() { Properties = properties }, defaultEmbeddingGenerator: null);
}
