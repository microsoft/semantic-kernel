// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Pgvector;
using Xunit;

namespace SemanticKernel.Connectors.Postgres.UnitTests;

/// <summary>
/// Unit tests for <see cref="PostgresVectorStoreRecordMapper{TRecord}"/> class.
/// </summary>
public sealed class PostgresVectorStoreRecordMapperTests
{
    [Fact]
    public void MapFromDataToStorageModelWithStringKeyReturnsValidStorageModel()
    {
        // Arrange
        var definition = GetRecordDefinition<string>();
        var propertyReader = GetPropertyReader<TestRecord<string>>(definition);
        var dataModel = GetDataModel<string>("key");

        var mapper = new PostgresVectorStoreRecordMapper<TestRecord<string>>(propertyReader);

        // Act
        var result = mapper.MapFromDataToStorageModel(dataModel);

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
        var definition = GetRecordDefinition<ulong>();
        var propertyReader = GetPropertyReader<TestRecord<ulong>>(definition);
        var dataModel = GetDataModel<ulong>(1);

        var mapper = new PostgresVectorStoreRecordMapper<TestRecord<ulong>>(propertyReader);

        // Act
        var result = mapper.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal((ulong)1, result["Key"]);
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
    public void MapFromStorageToDataModelWithStringKeyReturnsValidGenericModel(bool includeVectors)
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f]);
        var storageVector = PostgresVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        var storageModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",
            ["StringProperty"] = "Value1",
            ["IntProperty"] = 5,
            ["StringArray"] = new List<string> { "Value2", "Value3" },
            ["FloatVector"] = storageVector,
        };

        var definition = GetRecordDefinition<string>();
        var propertyReader = GetPropertyReader<TestRecord<string>>(definition);

        var mapper = new PostgresVectorStoreRecordMapper<TestRecord<string>>(propertyReader);

        // Act
        var result = mapper.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = includeVectors });

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
    public void MapFromStorageToDataModelWithNumericKeyReturnsValidGenericModel(bool includeVectors)
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f]);
        var storageVector = PostgresVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        var storageModel = new Dictionary<string, object?>
        {
            ["Key"] = (ulong)1,
            ["StringProperty"] = "Value1",
            ["IntProperty"] = 5,
            ["StringArray"] = new List<string> { "Value2", "Value3" },
            ["FloatVector"] = storageVector
        };

        var definition = GetRecordDefinition<ulong>();
        var propertyReader = GetPropertyReader<TestRecord<ulong>>(definition);

        var mapper = new PostgresVectorStoreRecordMapper<TestRecord<ulong>>(propertyReader);

        // Act
        var result = mapper.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = includeVectors });

        // Assert
        Assert.Equal((ulong)1, result.Key);
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

    private static VectorStoreRecordDefinition GetRecordDefinition<TKey>()
    {
        return new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(TKey)),
                new VectorStoreRecordDataProperty("StringProperty", typeof(string)),
                new VectorStoreRecordDataProperty("IntProperty", typeof(int)),
                new VectorStoreRecordDataProperty("StringArray", typeof(IEnumerable<string>)),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
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
            StringArray = new List<string> { "Value2", "Value3" },
            FloatVector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f])
        };
    }

    private static VectorStoreRecordPropertyReader GetPropertyReader<TRecord>(VectorStoreRecordDefinition definition)
    {
        return new VectorStoreRecordPropertyReader(typeof(TRecord), definition, new()
        {
            RequiresAtLeastOneVector = false,
            SupportsMultipleKeys = false,
            SupportsMultipleVectors = true
        });
    }

#pragma warning disable CA1812
    private sealed class TestRecord<TKey>
    {
        [VectorStoreRecordKey]
        public TKey? Key { get; set; }

        [VectorStoreRecordData]
        public string? StringProperty { get; set; }

        [VectorStoreRecordData]
        public int? IntProperty { get; set; }

        [VectorStoreRecordData]
        public IEnumerable<string>? StringArray { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction: DistanceFunction.CosineDistance)]
        public ReadOnlyMemory<float>? FloatVector { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}
