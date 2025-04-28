// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Contains tests for the <see cref="RedisVectorStoreCollectionSearchMapping"/> class.
/// </summary>
public class RedisVectorStoreCollectionSearchMappingTests
{
    [Fact]
    public void ValidateVectorAndConvertToBytesConvertsFloatVector()
    {
        // Arrange.
        var floatVector = new ReadOnlyMemory<float>(new float[] { 1.0f, 2.0f, 3.0f });

        // Act.
        var byteArray = RedisVectorStoreCollectionSearchMapping.ValidateVectorAndConvertToBytes(floatVector, "Test");

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
        var byteArray = RedisVectorStoreCollectionSearchMapping.ValidateVectorAndConvertToBytes(doubleVector, "Test");

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
            var byteArray = RedisVectorStoreCollectionSearchMapping.ValidateVectorAndConvertToBytes(unsupportedVector, "Test");
        });
        Assert.Equal("The provided vector type System.ReadOnlyMemory`1[[System.Int32, System.Private.CoreLib, Version=8.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]] is not supported by the Redis Test connector.", exception.Message);
    }

    [Fact]
    public void BuildQueryBuildsRedisQueryWithDefaults()
    {
        // Arrange.
        var floatVector = new ReadOnlyMemory<float>(new float[] { 1.0f, 2.0f, 3.0f });
        var byteArray = MemoryMarshal.AsBytes(floatVector.Span).ToArray();
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 10)
        ]);

        // Act.
        var query = RedisVectorStoreCollectionSearchMapping.BuildQuery(byteArray, top: 3, new VectorSearchOptions<DummyType>(), model, model.VectorProperty, null);

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
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 10) { StoragePropertyName = "storage_Vector" }
        ]);
        var selectFields = new string[] { "storage_Field1", "storage_Field2" };

        // Act.
        var query = RedisVectorStoreCollectionSearchMapping.BuildQuery(byteArray, top: 5, vectorSearchOptions, model, model.VectorProperty, selectFields);

        // Assert.
        Assert.NotNull(query);
        Assert.Equal("*=>[KNN 8 @storage_Vector $embedding AS vector_score]", query.QueryString);
    }

    [Theory]
    [InlineData("stringEquality")]
    [InlineData("intEquality")]
    [InlineData("longEquality")]
    [InlineData("floatEquality")]
    [InlineData("doubleEquality")]
    [InlineData("tagContains")]
    public void BuildFilterBuildsEqualityFilter(string filterType)
    {
        // Arrange.
        var basicVectorSearchFilter = filterType switch
        {
            "stringEquality" => new VectorSearchFilter().EqualTo("Data1", "my value"),
            "intEquality" => new VectorSearchFilter().EqualTo("Data1", 3),
            "longEquality" => new VectorSearchFilter().EqualTo("Data1", 3L),
            "floatEquality" => new VectorSearchFilter().EqualTo("Data1", 3.3f),
            "doubleEquality" => new VectorSearchFilter().EqualTo("Data1", 3.3),
            "tagContains" => new VectorSearchFilter().AnyTagEqualTo("Data1", "my value"),
            _ => throw new InvalidOperationException(),
        };

        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data1", typeof(string)) { StoragePropertyName = "storage_Data1" },
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 10)
        ]);

        // Act.
        var filter = RedisVectorStoreCollectionSearchMapping.BuildLegacyFilter(basicVectorSearchFilter, model);

        // Assert.
        switch (filterType)
        {
            case "stringEquality":
                Assert.Equal("(@storage_Data1:{my value})", filter);
                break;
            case "intEquality":
            case "longEquality":
                Assert.Equal("(@storage_Data1:[3 3])", filter);
                break;
            case "floatEquality":
            case "doubleEquality":
                Assert.Equal("(@storage_Data1:[3.3 3.3])", filter);
                break;
            case "tagContains":
                Assert.Equal("(@storage_Data1:{my value})", filter);
                break;
        }
    }

    [Fact]
    public void BuildFilterThrowsForInvalidValueType()
    {
        // Arrange.
        var basicVectorSearchFilter = new VectorSearchFilter().EqualTo("Data1", true);
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data1", typeof(string)) { StoragePropertyName = "storage_Data1" },
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 10)
        ]);

        // Act & Assert.
        Assert.Throws<InvalidOperationException>(() =>
        {
            var filter = RedisVectorStoreCollectionSearchMapping.BuildLegacyFilter(basicVectorSearchFilter, model);
        });
    }

    [Fact]
    public void BuildFilterThrowsForUnknownFieldName()
    {
        // Arrange.
        var basicVectorSearchFilter = new VectorSearchFilter().EqualTo("UnknownData", "value");
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data1", typeof(string)) { StoragePropertyName = "storage_Data1" },
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 10)
        ]);

        // Act & Assert.
        Assert.Throws<InvalidOperationException>(() =>
        {
            var filter = RedisVectorStoreCollectionSearchMapping.BuildLegacyFilter(basicVectorSearchFilter, model);
        });
    }

    [Fact]
    public void ResolveDistanceFunctionReturnsCosineSimilarityIfNoDistanceFunctionSpecified()
    {
        var property = new VectorStoreRecordVectorPropertyModel("Prop", typeof(ReadOnlyMemory<float>));

        // Act.
        var resolvedDistanceFunction = RedisVectorStoreCollectionSearchMapping.ResolveDistanceFunction(property);

        // Assert.
        Assert.Equal(DistanceFunction.CosineSimilarity, resolvedDistanceFunction);
    }

    [Fact]
    public void ResolveDistanceFunctionReturnsDistanceFunctionFromProvidedProperty()
    {
        var property = new VectorStoreRecordVectorPropertyModel("Prop", typeof(ReadOnlyMemory<float>)) { DistanceFunction = DistanceFunction.DotProductSimilarity };

        // Act.
        var resolvedDistanceFunction = RedisVectorStoreCollectionSearchMapping.ResolveDistanceFunction(property);

        // Assert.
        Assert.Equal(DistanceFunction.DotProductSimilarity, resolvedDistanceFunction);
    }

    [Fact]
    public void GetOutputScoreFromRedisScoreConvertsCosineDistanceToSimilarity()
    {
        // Act & Assert.
        Assert.Equal(-1, RedisVectorStoreCollectionSearchMapping.GetOutputScoreFromRedisScore(2, DistanceFunction.CosineSimilarity));
        Assert.Equal(0, RedisVectorStoreCollectionSearchMapping.GetOutputScoreFromRedisScore(1, DistanceFunction.CosineSimilarity));
        Assert.Equal(1, RedisVectorStoreCollectionSearchMapping.GetOutputScoreFromRedisScore(0, DistanceFunction.CosineSimilarity));
    }

    [Theory]
    [InlineData(DistanceFunction.CosineDistance, 2)]
    [InlineData(DistanceFunction.DotProductSimilarity, 2)]
    [InlineData(DistanceFunction.EuclideanSquaredDistance, 2)]
    public void GetOutputScoreFromRedisScoreLeavesNonConsineSimilarityUntouched(string distanceFunction, float score)
    {
        // Act & Assert.
        Assert.Equal(score, RedisVectorStoreCollectionSearchMapping.GetOutputScoreFromRedisScore(score, distanceFunction));
    }

#pragma warning disable CA1812 // An internal class that is apparently never instantiated. If so, remove the code from the assembly.
    private sealed class DummyType;
#pragma warning restore CA1812

    private static VectorStoreRecordModel BuildModel(List<VectorStoreRecordProperty> properties)
        => new VectorStoreRecordModelBuilder(RedisHashSetVectorStoreRecordCollection<string, DummyType>.ModelBuildingOptions)
            .Build(
                typeof(Dictionary<string, object?>),
                new() { Properties = properties },
                defaultEmbeddingGenerator: null);
}
