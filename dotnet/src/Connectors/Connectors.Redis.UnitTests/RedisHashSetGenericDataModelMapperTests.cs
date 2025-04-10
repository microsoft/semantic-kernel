// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using StackExchange.Redis;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisHashSetGenericDataModelMapper"/> class.
/// </summary>
public class RedisHashSetGenericDataModelMapperTests
{
    private static readonly float[] s_floatVector = new float[] { 1.0f, 2.0f, 3.0f, 4.0f };
    private static readonly double[] s_doubleVector = new double[] { 5.0d, 6.0d, 7.0d, 8.0d };

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange.
        var sut = new RedisHashSetGenericDataModelMapper(RedisHashSetVectorStoreMappingTestHelpers.s_vectorStoreRecordDefinition.Properties);
        var dataModel = new VectorStoreGenericDataModel<string>("key")
        {
            Data =
            {
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
            },
            Vectors =
            {
                ["FloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
                ["DoubleVector"] = new ReadOnlyMemory<double>(s_doubleVector),
            },
        };

        // Act.
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal("key", storageModel.Key);
        RedisHashSetVectorStoreMappingTestHelpers.VerifyHashSet(storageModel.HashEntries);
    }

    [Fact]
    public void MapFromDataToStorageModelMapsNullValues()
    {
        // Arrange
        VectorStoreRecordDefinition vectorStoreRecordDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("StringData", typeof(string)),
                new VectorStoreRecordDataProperty("NullableIntData", typeof(int?)),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>?), 10),
            },
        };

        var dataModel = new VectorStoreGenericDataModel<string>("key")
        {
            Data =
            {
                ["StringData"] = null,
                ["NullableIntData"] = null,
            },
            Vectors =
            {
                ["FloatVector"] = null,
            },
        };

        var sut = new RedisHashSetGenericDataModelMapper(RedisHashSetVectorStoreMappingTestHelpers.s_vectorStoreRecordDefinition.Properties);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal("key", storageModel.Key);

        Assert.Equal("storage_string_data", storageModel.HashEntries[0].Name.ToString());
        Assert.True(storageModel.HashEntries[0].Value.IsNull);

        Assert.Equal("NullableIntData", storageModel.HashEntries[1].Name.ToString());
        Assert.True(storageModel.HashEntries[1].Value.IsNull);

        Assert.Equal("FloatVector", storageModel.HashEntries[2].Name.ToString());
        Assert.True(storageModel.HashEntries[2].Value.IsNull);
    }

    [Fact]
    public void MapFromStorageToDataModelMapsAllSupportedTypes()
    {
        // Arrange.
        var hashSet = RedisHashSetVectorStoreMappingTestHelpers.CreateHashSet();

        var sut = new RedisHashSetGenericDataModelMapper(RedisHashSetVectorStoreMappingTestHelpers.s_vectorStoreRecordDefinition.Properties);

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", hashSet), new() { IncludeVectors = true });

        // Assert.
        Assert.Equal("key", dataModel.Key);
        Assert.Equal("data 1", dataModel.Data["StringData"]);
        Assert.Equal(1, dataModel.Data["IntData"]);
        Assert.Equal(2u, dataModel.Data["UIntData"]);
        Assert.Equal(3L, dataModel.Data["LongData"]);
        Assert.Equal(4ul, dataModel.Data["ULongData"]);
        Assert.Equal(5.5d, dataModel.Data["DoubleData"]);
        Assert.Equal(6.6f, dataModel.Data["FloatData"]);
        Assert.True((bool)dataModel.Data["BoolData"]!);
        Assert.Equal(7, dataModel.Data["NullableIntData"]);
        Assert.Equal(8u, dataModel.Data["NullableUIntData"]);
        Assert.Equal(9L, dataModel.Data["NullableLongData"]);
        Assert.Equal(10ul, dataModel.Data["NullableULongData"]);
        Assert.Equal(11.1d, dataModel.Data["NullableDoubleData"]);
        Assert.Equal(12.2f, dataModel.Data["NullableFloatData"]);
        Assert.False((bool)dataModel.Data["NullableBoolData"]!);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, ((ReadOnlyMemory<float>)dataModel.Vectors["FloatVector"]!).ToArray());
        Assert.Equal(new double[] { 5, 6, 7, 8 }, ((ReadOnlyMemory<double>)dataModel.Vectors["DoubleVector"]!).ToArray());
    }

    [Fact]
    public void MapFromStorageToDataModelMapsNullValues()
    {
        // Arrange
        VectorStoreRecordDefinition vectorStoreRecordDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("StringData", typeof(string)),
                new VectorStoreRecordDataProperty("NullableIntData", typeof(int?)),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>?), 10),
            },
        };

        var hashSet = new HashEntry[]
        {
            new("storage_string_data", RedisValue.Null),
            new("NullableIntData", RedisValue.Null),
            new("FloatVector", RedisValue.Null),
        };

        var sut = new RedisHashSetGenericDataModelMapper(RedisHashSetVectorStoreMappingTestHelpers.s_vectorStoreRecordDefinition.Properties);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(("key", hashSet), new() { IncludeVectors = true });

        // Assert
        Assert.Equal("key", dataModel.Key);
        Assert.Null(dataModel.Data["StringData"]);
        Assert.Null(dataModel.Data["NullableIntData"]);
        Assert.Null(dataModel.Vectors["FloatVector"]);
    }

    [Fact]
    public void MapFromDataToStorageModelSkipsMissingProperties()
    {
        // Arrange.
        var sut = new RedisHashSetGenericDataModelMapper(RedisHashSetVectorStoreMappingTestHelpers.s_vectorStoreRecordDefinition.Properties);
        var dataModel = new VectorStoreGenericDataModel<string>("key")
        {
            Data = { },
            Vectors = { },
        };

        // Act.
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal("key", storageModel.Key);
        Assert.Empty(storageModel.HashEntries);
    }

    [Fact]
    public void MapFromStorageToDataModelSkipsMissingProperties()
    {
        // Arrange.
        var hashSet = Array.Empty<HashEntry>();

        var sut = new RedisHashSetGenericDataModelMapper(RedisHashSetVectorStoreMappingTestHelpers.s_vectorStoreRecordDefinition.Properties);

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", hashSet), new() { IncludeVectors = true });

        // Assert.
        Assert.Equal("key", dataModel.Key);
        Assert.Empty(dataModel.Data);
        Assert.Empty(dataModel.Vectors);
    }
}
