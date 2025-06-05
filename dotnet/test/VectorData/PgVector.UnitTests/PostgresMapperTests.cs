// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel.Connectors.PgVector;
using Pgvector;
using Xunit;

namespace SemanticKernel.Connectors.PgVector.UnitTests;

/// <summary>
/// Unit tests for <see cref="PostgresMapper{TRecord}"/> class.
/// </summary>
public sealed class PostgresMapperTests
{
    [Fact]
    public void MapFromDataToStorageModelWithStringKeyReturnsValidStorageModel()
    {
        // Arrange
        var definition = GetRecordDefinition<string>();
        var model = GetModel<TestRecord<string>>(definition);
        var dataModel = GetRecord<string>("key");

        var mapper = new PostgresMapper<TestRecord<string>>(model);

        // Act
        var result = mapper.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal("key", result["Key"]);
        Assert.Equal("Value1", result["StringProperty"]);
        Assert.Equal(5, result["IntProperty"]);
        Assert.Equal(new List<string> { "Value2", "Value3" }, result["StringArray"]);

        Vector? vector = result["FloatVector"] as Vector;

        Assert.NotNull(vector);
        Assert.True(vector.ToArray().Length > 0);
    }

    [Fact]
    public void MapFromDataToStorageModelWithNumericKeyReturnsValidStorageModel()
    {
        // Arrange
        var definition = GetRecordDefinition<long>();
        var propertyReader = GetModel<TestRecord<long>>(definition);
        var dataModel = GetRecord<long>(1);

        var mapper = new PostgresMapper<TestRecord<long>>(propertyReader);

        // Act
        var result = mapper.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal(1L, result["Key"]);
        Assert.Equal("Value1", result["StringProperty"]);
        Assert.Equal(5, result["IntProperty"]);
        Assert.Equal(new List<string> { "Value2", "Value3" }, result["StringArray"]);

        var vector = result["FloatVector"] as Vector;

        Assert.NotNull(vector);
        Assert.True(vector.ToArray().Length > 0);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapFromStorageToDataModelWithStringKeyReturnsValidDynamicModel(bool includeVectors)
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f]);
        var storageVector = PostgresPropertyMapping.MapVectorForStorageModel(vector);

        var storageModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",
            ["StringProperty"] = "Value1",
            ["IntProperty"] = 5,
            ["StringArray"] = new List<string> { "Value2", "Value3" },
            ["FloatVector"] = storageVector,
        };

        var definition = GetRecordDefinition<string>();
        var propertyReader = GetModel<TestRecord<string>>(definition);

        var mapper = new PostgresMapper<TestRecord<string>>(propertyReader);

        // Act
        var result = mapper.MapFromStorageToDataModel(storageModel, includeVectors);

        // Assert
        Assert.Equal("key", result.Key);
        Assert.Equal("Value1", result.StringProperty);
        Assert.Equal(5, result.IntProperty);
        Assert.Equal(new List<string> { "Value2", "Value3" }, result.StringArray);

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
        var storageVector = PostgresPropertyMapping.MapVectorForStorageModel(vector);

        var storageModel = new Dictionary<string, object?>
        {
            ["Key"] = 1L,
            ["StringProperty"] = "Value1",
            ["IntProperty"] = 5,
            ["StringArray"] = new List<string> { "Value2", "Value3" },
            ["FloatVector"] = storageVector
        };

        var definition = GetRecordDefinition<long>();
        var propertyReader = GetModel<TestRecord<long>>(definition);

        var mapper = new PostgresMapper<TestRecord<long>>(propertyReader);

        // Act
        var result = mapper.MapFromStorageToDataModel(storageModel, includeVectors);

        // Assert
        Assert.Equal(1L, result.Key);
        Assert.Equal("Value1", result.StringProperty);
        Assert.Equal(5, result.IntProperty);
        Assert.Equal(new List<string> { "Value2", "Value3" }, result.StringArray);

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
                new VectorStoreDataProperty("StringArray", typeof(List<string>)),
                new VectorStoreVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
            }
        };
    }

    private static TestRecord<TKey> GetRecord<TKey>(TKey key)
    {
        return new TestRecord<TKey>
        {
            Key = key,
            StringProperty = "Value1",
            IntProperty = 5,
            StringArray = new List<string> { "Value2", "Value3" },
            FloatVector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f])
        };
    }

    private static CollectionModel GetModel<TRecord>(VectorStoreCollectionDefinition definition)
        => new PostgresModelBuilder().Build(typeof(TRecord), definition, defaultEmbeddingGenerator: null);

#pragma warning disable CA1812
    private sealed class TestRecord<TKey>
    {
        [VectorStoreKey]
        public TKey? Key { get; set; }

        [VectorStoreData]
        public string? StringProperty { get; set; }

        [VectorStoreData]
        public int? IntProperty { get; set; }

        [VectorStoreData]
        public List<string>? StringArray { get; set; }

        [VectorStoreVector(Dimensions: 4, DistanceFunction = DistanceFunction.CosineDistance)]
        public ReadOnlyMemory<float>? FloatVector { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}
