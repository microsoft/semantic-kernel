// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using StackExchange.Redis;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains dynamic mapping tests for the <see cref="RedisHashSetMapper{TConsumerDataModel}"/> class.
/// </summary>
public class RedisHashSetDynamicMappingTests
{
    private static readonly CollectionModel s_model = BuildModel(RedisHashSetMappingTestHelpers.s_definition);

    private static readonly float[] s_floatVector = new float[] { 1.0f, 2.0f, 3.0f, 4.0f };
    private static readonly double[] s_doubleVector = new double[] { 5.0d, 6.0d, 7.0d, 8.0d };

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange.
        var sut = new RedisHashSetMapper<Dictionary<string, object?>>(s_model);
        var dataModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",

            ["StringData"] = "data 1",
            ["IntData"] = 1,
            ["UIntData"] = 2u,
            ["LongData"] = 3L,
            ["ULongData"] = 4ul,
            ["DoubleData"] = 5.5d,
            ["FloatData"] = 6.6f,
            ["BoolData"] = true,
            ["NullableIntData"] = 7,
            ["NullableUIntData"] = 8u,
            ["NullableLongData"] = 9L,
            ["NullableULongData"] = 10ul,
            ["NullableDoubleData"] = 11.1d,
            ["NullableFloatData"] = 12.2f,
            ["NullableBoolData"] = false,

            ["FloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
            ["DoubleVector"] = new ReadOnlyMemory<double>(s_doubleVector),
        };

        // Act.
        var storageModel = sut.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal("key", storageModel.Key);
        RedisHashSetMappingTestHelpers.VerifyHashSet(storageModel.HashEntries);
    }

    [Fact]
    public void MapFromDataToStorageModelMapsNullValues()
    {
        // Arrange
        CollectionModel model = BuildModel(new()
        {
            Properties = new List<VectorStoreProperty>
            {
                new VectorStoreKeyProperty("Key", typeof(string)),
                new VectorStoreDataProperty("StringData", typeof(string)) { StorageName = "storage_string_data" },
                new VectorStoreDataProperty("NullableIntData", typeof(int?)),
                new VectorStoreVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>?), 10),
            },
        });

        var dataModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",
            ["StringData"] = null,
            ["NullableIntData"] = null,
            ["FloatVector"] = null,
        };

        var sut = new RedisHashSetMapper<Dictionary<string, object?>>(model);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal("key", storageModel.Key);

        Assert.Equal("storage_string_data", storageModel.HashEntries[0].Name.ToString());
        Assert.True(storageModel.HashEntries[0].Value.IsNull);

        Assert.Equal("NullableIntData", storageModel.HashEntries[1].Name.ToString());
        Assert.True(storageModel.HashEntries[1].Value.IsNull);
    }

    [Fact]
    public void MapFromStorageToDataModelMapsAllSupportedTypes()
    {
        // Arrange.
        var hashSet = RedisHashSetMappingTestHelpers.CreateHashSet();
        var sut = new RedisHashSetMapper<Dictionary<string, object?>>(s_model);

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", hashSet), includeVectors: true);

        // Assert.
        Assert.Equal("key", dataModel["Key"]);
        Assert.Equal("data 1", dataModel["StringData"]);
        Assert.Equal(1, dataModel["IntData"]);
        Assert.Equal(2u, dataModel["UIntData"]);
        Assert.Equal(3L, dataModel["LongData"]);
        Assert.Equal(4ul, dataModel["ULongData"]);
        Assert.Equal(5.5d, dataModel["DoubleData"]);
        Assert.Equal(6.6f, dataModel["FloatData"]);
        Assert.True((bool)dataModel["BoolData"]!);
        Assert.Equal(7, dataModel["NullableIntData"]);
        Assert.Equal(8u, dataModel["NullableUIntData"]);
        Assert.Equal(9L, dataModel["NullableLongData"]);
        Assert.Equal(10ul, dataModel["NullableULongData"]);
        Assert.Equal(11.1d, dataModel["NullableDoubleData"]);
        Assert.Equal(12.2f, dataModel["NullableFloatData"]);
        Assert.False((bool)dataModel["NullableBoolData"]!);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, ((ReadOnlyMemory<float>)dataModel["FloatVector"]!).ToArray());
        Assert.Equal(new double[] { 5, 6, 7, 8 }, ((ReadOnlyMemory<double>)dataModel["DoubleVector"]!).ToArray());
    }

    [Fact]
    public void MapFromStorageToDataModelMapsNullValues()
    {
        // Arrange
        var model = BuildModel(new()
        {
            Properties = new List<VectorStoreProperty>
            {
                new VectorStoreKeyProperty("Key", typeof(string)),
                new VectorStoreDataProperty("StringData", typeof(string)) { StorageName = "storage_string_data" },
                new VectorStoreDataProperty("NullableIntData", typeof(int?)),
                new VectorStoreVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>?), 10),
            }
        });

        var hashSet = new HashEntry[]
        {
            new("storage_string_data", RedisValue.Null),
            new("NullableIntData", RedisValue.Null),
            new("FloatVector", RedisValue.Null),
        };

        var sut = new RedisHashSetMapper<Dictionary<string, object?>>(model);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(("key", hashSet), includeVectors: true);

        // Assert
        Assert.Equal("key", dataModel["Key"]);
        Assert.Null(dataModel["StringData"]);
        Assert.Null(dataModel["NullableIntData"]);
        Assert.Null(dataModel["FloatVector"]);
    }

    [Fact]
    public void MapFromDataToStorageModelSkipsMissingProperties()
    {
        // Arrange.
        var model = BuildModel(new()
        {
            Properties = new List<VectorStoreProperty>
            {
                new VectorStoreKeyProperty("Key", typeof(string)),
                new VectorStoreDataProperty("StringData", typeof(string)) { StorageName = "storage_string_data" },
                new VectorStoreDataProperty("NullableIntData", typeof(int?)),
                new VectorStoreVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>?), 10),
            }
        });

        var sut = new RedisHashSetMapper<Dictionary<string, object?>>(model);
        var dataModel = new Dictionary<string, object?> { ["Key"] = "key" };

        // Act.
        var storageModel = sut.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal("key", storageModel.Key);

        Assert.Equal("storage_string_data", storageModel.HashEntries[0].Name.ToString());
        Assert.True(storageModel.HashEntries[0].Value.IsNull);

        Assert.Equal("NullableIntData", storageModel.HashEntries[1].Name.ToString());
        Assert.True(storageModel.HashEntries[1].Value.IsNull);
    }

    [Fact]
    public void MapFromStorageToDataModelSkipsMissingProperties()
    {
        // Arrange.
        var hashSet = Array.Empty<HashEntry>();

        var sut = new RedisHashSetMapper<Dictionary<string, object?>>(s_model);

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", hashSet), includeVectors: true);

        // Assert.
        Assert.Single(dataModel);
        Assert.Equal("key", dataModel["Key"]);
    }

    private static CollectionModel BuildModel(VectorStoreCollectionDefinition definition)
        => new RedisModelBuilder(RedisHashSetCollection<object, Dictionary<string, object?>>.ModelBuildingOptions)
            .BuildDynamic(definition, defaultEmbeddingGenerator: null);
}
