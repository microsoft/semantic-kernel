// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel.Connectors.SqliteVec;
using Xunit;

namespace SemanticKernel.Connectors.SqliteVec.UnitTests;

/// <summary>
/// Unit tests for <see cref="SqliteMapper{TRecord}"/> class.
/// </summary>
public sealed class SqliteMapperTests
{
    [Fact]
    public void MapFromDataToStorageModelWithStringKeyReturnsValidStorageModel()
    {
        // Arrange
        var definition = GetRecordDefinition<string>();
        var model = BuildModel(typeof(TestRecord<string>), definition);
        var dataModel = GetDataModel<string>("key");

        var mapper = new SqliteMapper<TestRecord<string>>(model);

        // Act
        var result = mapper.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal("key", result["Key"]);
        Assert.Equal("Value1", result["StringProperty"]);
        Assert.Equal(5, result["IntProperty"]);

        var vectorBytes = result["FloatVector"] as byte[];

        Assert.NotNull(vectorBytes);
        Assert.True(vectorBytes.Length > 0);
    }

    [Fact]
    public void MapFromDataToStorageModelWithNumericKeyReturnsValidStorageModel()
    {
        // Arrange
        var definition = GetRecordDefinition<long>();
        var model = BuildModel(typeof(TestRecord<long>), definition);
        var dataModel = GetDataModel<long>(1);

        var mapper = new SqliteMapper<TestRecord<long>>(model);

        // Act
        var result = mapper.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal((long)1, result["Key"]);
        Assert.Equal("Value1", result["StringProperty"]);
        Assert.Equal(5, result["IntProperty"]);

        var vectorBytes = result["FloatVector"] as byte[];

        Assert.NotNull(vectorBytes);
        Assert.True(vectorBytes.Length > 0);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapFromStorageToDataModelWithStringKeyReturnsValidDynamicModel(bool includeVectors)
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f]);
        var storageVector = SqlitePropertyMapping.MapVectorForStorageModel(vector);

        var storageModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",
            ["StringProperty"] = "Value1",
            ["IntProperty"] = 5,
            ["FloatVector"] = storageVector
        };

        var definition = GetRecordDefinition<string>();
        var model = BuildModel(typeof(TestRecord<string>), definition);

        var mapper = new SqliteMapper<TestRecord<string>>(model);

        // Act
        var result = mapper.MapFromStorageToDataModel(storageModel, includeVectors);

        // Assert
        Assert.Equal("key", result.Key);
        Assert.Equal("Value1", result.StringProperty);
        Assert.Equal(5, result.IntProperty);

        if (includeVectors)
        {
            Assert.NotNull(result.FloatVector);
            Assert.Equal(vector.Span.ToArray(), result.FloatVector.Value.Span.ToArray());
        }
        else
        {
            Assert.Null(result.FloatVector);
        }
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapFromStorageToDataModelWithNumericKeyReturnsValidDynamicModel(bool includeVectors)
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f]);
        var storageVector = SqlitePropertyMapping.MapVectorForStorageModel(vector);

        var storageModel = new Dictionary<string, object?>
        {
            ["Key"] = (long)1,
            ["StringProperty"] = "Value1",
            ["IntProperty"] = 5,
            ["FloatVector"] = storageVector
        };

        var definition = GetRecordDefinition<long>();
        var model = BuildModel(typeof(TestRecord<long>), definition);

        var mapper = new SqliteMapper<TestRecord<long>>(model);

        // Act
        var result = mapper.MapFromStorageToDataModel(storageModel, includeVectors);

        // Assert
        Assert.Equal((long)1, result.Key);
        Assert.Equal("Value1", result.StringProperty);
        Assert.Equal(5, result.IntProperty);

        if (includeVectors)
        {
            Assert.NotNull(result.FloatVector);
            Assert.Equal(vector.Span.ToArray(), result.FloatVector.Value.Span.ToArray());
        }
        else
        {
            Assert.Null(result.FloatVector);
        }
    }

    #region private

    private static VectorStoreCollectionDefinition GetRecordDefinition<TKey>()
    {
        return new VectorStoreCollectionDefinition
        {
            Properties = new List<VectorStoreProperty>
            {
                new VectorStoreKeyProperty("Key", typeof(TKey)),
                new VectorStoreDataProperty("StringProperty", typeof(string)),
                new VectorStoreDataProperty("IntProperty", typeof(int)),
                new VectorStoreVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
            }
        };
    }

    private static TestRecord<TKey> GetDataModel<TKey>(TKey key)
    {
        return new TestRecord<TKey>
        {
            Key = key,
            StringProperty = "Value1",
            IntProperty = 5,
            FloatVector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f])
        };
    }

    private static CollectionModel BuildModel(Type type, VectorStoreCollectionDefinition definition)
        => new SqliteModelBuilder().Build(type, definition, defaultEmbeddingGenerator: null);

#pragma warning disable CA1812
    private sealed class TestRecord<TKey>
    {
        [VectorStoreKey]
        public TKey? Key { get; set; }

        [VectorStoreData]
        public string? StringProperty { get; set; }

        [VectorStoreData]
        public int? IntProperty { get; set; }

        [VectorStoreVector(Dimensions: 4, DistanceFunction = DistanceFunction.CosineDistance)]
        public ReadOnlyMemory<float>? FloatVector { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}
