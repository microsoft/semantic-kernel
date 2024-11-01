// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Pgvector;
using Xunit;

namespace SemanticKernel.Connectors.Postgres.UnitTests;

/// <summary>
/// Unit tests for <see cref="PostgresGenericDataModelMapper{T}"/> class.
/// </summary>
public sealed class PostgresGenericDataModelMapperTests
{
    [Fact]
    public void MapFromDataToStorageModelWithStringKeyReturnsValidStorageModel()
    {
        // Arrange
        var definition = GetRecordDefinition<string>();
        var propertyReader = GetPropertyReader<VectorStoreGenericDataModel<string>>(definition);
        var dataModel = GetGenericDataModel<string>("key");

        var mapper = new PostgresGenericDataModelMapper<string>(propertyReader);

        // Act
        var result = mapper.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal("key", result["Key"]);
        Assert.Equal("Value1", result["StringProperty"]);
        Assert.Equal(5, result["IntProperty"]);

        var vector = result["FloatVector"] as Vector;

        Assert.NotNull(vector);
        Assert.True(vector.ToArray().Length > 0);
    }

    [Fact]
    public void MapFromDataToStorageModelWithNumericKeyReturnsValidStorageModel()
    {
        // Arrange
        var definition = GetRecordDefinition<int>();
        var propertyReader = GetPropertyReader<VectorStoreGenericDataModel<string>>(definition);
        var dataModel = GetGenericDataModel<int>(1);

        var mapper = new PostgresGenericDataModelMapper<int>(propertyReader);

        // Act
        var result = mapper.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal(1, result["Key"]);
        Assert.Equal("Value1", result["StringProperty"]);
        Assert.Equal(5, result["IntProperty"]);

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
            ["FloatVector"] = storageVector
        };

        var definition = GetRecordDefinition<string>();
        var propertyReader = GetPropertyReader<VectorStoreGenericDataModel<string>>(definition);

        var mapper = new PostgresGenericDataModelMapper<string>(propertyReader);

        // Act
        var result = mapper.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = includeVectors });

        // Assert
        Assert.Equal("key", result.Key);
        Assert.Equal("Value1", result.Data["StringProperty"]);
        Assert.Equal(5, result.Data["IntProperty"]);

        if (includeVectors)
        {
            Assert.NotNull(result.Vectors["FloatVector"]);
            Assert.Equal(vector.ToArray(), ((ReadOnlyMemory<float>)result.Vectors["FloatVector"]!).ToArray());
        }
        else
        {
            Assert.False(result.Vectors.ContainsKey("FloatVector"));
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
            ["Key"] = 1,
            ["StringProperty"] = "Value1",
            ["IntProperty"] = 5,
            ["FloatVector"] = storageVector
        };

        var definition = GetRecordDefinition<int>();
        var propertyReader = GetPropertyReader<VectorStoreGenericDataModel<int>>(definition);

        var mapper = new PostgresGenericDataModelMapper<int>(propertyReader);

        // Act
        var result = mapper.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = includeVectors });

        // Assert
        Assert.Equal(1, result.Key);
        Assert.Equal("Value1", result.Data["StringProperty"]);
        Assert.Equal(5, result.Data["IntProperty"]);

        if (includeVectors)
        {
            Assert.NotNull(result.Vectors["FloatVector"]);
            Assert.Equal(vector.ToArray(), ((ReadOnlyMemory<float>)result.Vectors["FloatVector"]!).ToArray());
        }
        else
        {
            Assert.False(result.Vectors.ContainsKey("FloatVector"));
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
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
            }
        };
    }

    private static VectorStoreGenericDataModel<TKey> GetGenericDataModel<TKey>(TKey key)
    {
        return new VectorStoreGenericDataModel<TKey>(key)
        {
            Data = new()
            {
                ["StringProperty"] = "Value1",
                ["IntProperty"] = 5
            },
            Vectors = new()
            {
                ["FloatVector"] = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f])
            }
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

    #endregion
}
