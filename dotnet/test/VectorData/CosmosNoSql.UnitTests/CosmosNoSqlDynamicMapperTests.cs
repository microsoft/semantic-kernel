// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using Xunit;

namespace SemanticKernel.Connectors.CosmosNoSql.UnitTests;

/// <summary>
/// Unit tests for <see cref="CosmosNoSqlDynamicMapper"/> class.
/// </summary>
public sealed class CosmosNoSqlDynamicMapperTests
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = JsonSerializerOptions.Default;

    private static readonly CollectionModel s_model = new CosmosNoSqlModelBuilder()
        .BuildDynamic(
            new VectorStoreCollectionDefinition
            {
                Properties =
                [
                    new VectorStoreKeyProperty("Key", typeof(string)),
                    new VectorStoreDataProperty("BoolDataProp", typeof(bool)),
                    new VectorStoreDataProperty("NullableBoolDataProp", typeof(bool?)),
                    new VectorStoreDataProperty("StringDataProp", typeof(string)),
                    new VectorStoreDataProperty("IntDataProp", typeof(int)),
                    new VectorStoreDataProperty("NullableIntDataProp", typeof(int?)),
                    new VectorStoreDataProperty("LongDataProp", typeof(long)),
                    new VectorStoreDataProperty("NullableLongDataProp", typeof(long?)),
                    new VectorStoreDataProperty("FloatDataProp", typeof(float)),
                    new VectorStoreDataProperty("NullableFloatDataProp", typeof(float?)),
                    new VectorStoreDataProperty("DoubleDataProp", typeof(double)),
                    new VectorStoreDataProperty("NullableDoubleDataProp", typeof(double?)),
                    new VectorStoreDataProperty("DateTimeOffsetDataProp", typeof(DateTimeOffset)),
                    new VectorStoreDataProperty("NullableDateTimeOffsetDataProp", typeof(DateTimeOffset?)),
                    new VectorStoreDataProperty("TagListDataProp", typeof(List<string>)),
                    new VectorStoreVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
                    new VectorStoreVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10),
                    new VectorStoreVectorProperty("ByteVector", typeof(ReadOnlyMemory<byte>), 10),
                    new VectorStoreVectorProperty("NullableByteVector", typeof(ReadOnlyMemory<byte>?), 10),
                    new VectorStoreVectorProperty("SByteVector", typeof(ReadOnlyMemory<sbyte>), 10),
                    new VectorStoreVectorProperty("NullableSByteVector", typeof(ReadOnlyMemory<sbyte>?), 10),
                ],
            },
            defaultEmbeddingGenerator: null);

    private static readonly float[] s_floatVector = [1.0f, 2.0f, 3.0f];
    private static readonly byte[] s_byteVector = [1, 2, 3];
    private static readonly sbyte[] s_sbyteVector = [1, 2, 3];
    private static readonly List<string> s_taglist = ["tag1", "tag2"];

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange
        var sut = new CosmosNoSqlDynamicMapper(s_model, s_jsonSerializerOptions);

        var dataModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",

            ["BoolDataProp"] = true,
            ["NullableBoolDataProp"] = false,
            ["StringDataProp"] = "string",
            ["IntDataProp"] = 1,
            ["NullableIntDataProp"] = 2,
            ["LongDataProp"] = 3L,
            ["NullableLongDataProp"] = 4L,
            ["FloatDataProp"] = 5.0f,
            ["NullableFloatDataProp"] = 6.0f,
            ["DoubleDataProp"] = 7.0,
            ["NullableDoubleDataProp"] = 8.0,
            ["DateTimeOffsetDataProp"] = new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero),
            ["NullableDateTimeOffsetDataProp"] = new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero),
            ["TagListDataProp"] = s_taglist,

            ["FloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
            ["NullableFloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
            ["ByteVector"] = new ReadOnlyMemory<byte>(s_byteVector),
            ["NullableByteVector"] = new ReadOnlyMemory<byte>(s_byteVector),
            ["SByteVector"] = new ReadOnlyMemory<sbyte>(s_sbyteVector),
            ["NullableSByteVector"] = new ReadOnlyMemory<sbyte>(s_sbyteVector)
        };

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal("key", (string?)storageModel["id"]);
        Assert.Equal(true, (bool?)storageModel["BoolDataProp"]);
        Assert.Equal(false, (bool?)storageModel["NullableBoolDataProp"]);
        Assert.Equal("string", (string?)storageModel["StringDataProp"]);
        Assert.Equal(1, (int?)storageModel["IntDataProp"]);
        Assert.Equal(2, (int?)storageModel["NullableIntDataProp"]);
        Assert.Equal(3L, (long?)storageModel["LongDataProp"]);
        Assert.Equal(4L, (long?)storageModel["NullableLongDataProp"]);
        Assert.Equal(5.0f, (float?)storageModel["FloatDataProp"]);
        Assert.Equal(6.0f, (float?)storageModel["NullableFloatDataProp"]);
        Assert.Equal(7.0, (double?)storageModel["DoubleDataProp"]);
        Assert.Equal(8.0, (double?)storageModel["NullableDoubleDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), (DateTimeOffset?)storageModel["DateTimeOffsetDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), (DateTimeOffset?)storageModel["NullableDateTimeOffsetDataProp"]);
        Assert.Equal(s_taglist, storageModel["TagListDataProp"]!.AsArray().GetValues<string>().ToArray());
        Assert.Equal(s_floatVector, storageModel["FloatVector"]!.AsArray().GetValues<float>().ToArray());
        Assert.Equal(s_floatVector, storageModel["NullableFloatVector"]!.AsArray().GetValues<float>().ToArray());
        Assert.Equal(s_byteVector, storageModel["ByteVector"]!.AsArray().GetValues<byte>().ToArray());
        Assert.Equal(s_byteVector, storageModel["NullableByteVector"]!.AsArray().GetValues<byte>().ToArray());
        Assert.Equal(s_sbyteVector, storageModel["SByteVector"]!.AsArray().GetValues<sbyte>().ToArray());
        Assert.Equal(s_sbyteVector, storageModel["NullableSByteVector"]!.AsArray().GetValues<sbyte>().ToArray());
    }

    [Fact]
    public void MapFromDataToStorageModelMapsNullValues()
    {
        // Arrange
        VectorStoreCollectionDefinition definition = new()
        {
            Properties =
            [
                new VectorStoreKeyProperty("Key", typeof(string)),
                new VectorStoreDataProperty("StringDataProp", typeof(string)),
                new VectorStoreDataProperty("NullableIntDataProp", typeof(int?)),
                new VectorStoreVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10),
            ],
        };

        var dataModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",
            ["StringDataProp"] = null,
            ["NullableIntDataProp"] = null,
            ["NullableFloatVector"] = null
        };

        var sut = new CosmosNoSqlDynamicMapper(s_model, s_jsonSerializerOptions);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Null(storageModel["StringDataProp"]);
        Assert.Null(storageModel["NullableIntDataProp"]);
        Assert.Null(storageModel["NullableFloatVector"]);
    }

    [Fact]
    public void MapFromStorageToDataModelMapsAllSupportedTypes()
    {
        // Arrange
        var sut = new CosmosNoSqlDynamicMapper(s_model, s_jsonSerializerOptions);

        var storageModel = new JsonObject
        {
            ["id"] = "key",
            ["BoolDataProp"] = true,
            ["NullableBoolDataProp"] = false,
            ["StringDataProp"] = "string",
            ["IntDataProp"] = 1,
            ["NullableIntDataProp"] = 2,
            ["LongDataProp"] = 3L,
            ["NullableLongDataProp"] = 4L,
            ["FloatDataProp"] = 5.0f,
            ["NullableFloatDataProp"] = 6.0f,
            ["DoubleDataProp"] = 7.0,
            ["NullableDoubleDataProp"] = 8.0,
            ["DateTimeOffsetDataProp"] = new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero),
            ["NullableDateTimeOffsetDataProp"] = new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero),
            ["TagListDataProp"] = new JsonArray(s_taglist.Select(l => (JsonValue)l).ToArray()),
            ["FloatVector"] = new JsonArray(s_floatVector.Select(l => (JsonValue)l).ToArray()),
            ["NullableFloatVector"] = new JsonArray(s_floatVector.Select(l => (JsonValue)l).ToArray()),
            ["ByteVector"] = new JsonArray(s_byteVector.Select(l => (JsonValue)l).ToArray()),
            ["NullableByteVector"] = new JsonArray(s_byteVector.Select(l => (JsonValue)l).ToArray()),
            ["SByteVector"] = new JsonArray(s_sbyteVector.Select(l => (JsonValue)l).ToArray()),
            ["NullableSByteVector"] = new JsonArray(s_sbyteVector.Select(l => (JsonValue)l).ToArray())
        };

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, includeVectors: true);

        // Assert
        Assert.Equal("key", dataModel["Key"]);
        Assert.Equal(true, dataModel["BoolDataProp"]);
        Assert.Equal(false, dataModel["NullableBoolDataProp"]);
        Assert.Equal("string", dataModel["StringDataProp"]);
        Assert.Equal(1, dataModel["IntDataProp"]);
        Assert.Equal(2, dataModel["NullableIntDataProp"]);
        Assert.Equal(3L, dataModel["LongDataProp"]);
        Assert.Equal(4L, dataModel["NullableLongDataProp"]);
        Assert.Equal(5.0f, dataModel["FloatDataProp"]);
        Assert.Equal(6.0f, dataModel["NullableFloatDataProp"]);
        Assert.Equal(7.0, dataModel["DoubleDataProp"]);
        Assert.Equal(8.0, dataModel["NullableDoubleDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), dataModel["DateTimeOffsetDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), dataModel["NullableDateTimeOffsetDataProp"]);
        Assert.Equal(s_taglist, dataModel["TagListDataProp"]);
        Assert.Equal(s_floatVector, ((ReadOnlyMemory<float>)dataModel["FloatVector"]!).ToArray());
        Assert.Equal(s_floatVector, ((ReadOnlyMemory<float>)dataModel["NullableFloatVector"]!)!.ToArray());
        Assert.Equal(s_byteVector, ((ReadOnlyMemory<byte>)dataModel["ByteVector"]!).ToArray());
        Assert.Equal(s_byteVector, ((ReadOnlyMemory<byte>)dataModel["NullableByteVector"]!)!.ToArray());
        Assert.Equal(s_sbyteVector, ((ReadOnlyMemory<sbyte>)dataModel["SByteVector"]!).ToArray());
        Assert.Equal(s_sbyteVector, ((ReadOnlyMemory<sbyte>)dataModel["NullableSByteVector"]!)!.ToArray());
    }

    [Fact]
    public void MapFromStorageToDataModelMapsNullValues()
    {
        // Arrange
        VectorStoreCollectionDefinition definition = new()
        {
            Properties =
            [
                new VectorStoreKeyProperty("Key", typeof(string)),
                new VectorStoreDataProperty("StringDataProp", typeof(string)),
                new VectorStoreDataProperty("NullableIntDataProp", typeof(int?)),
                new VectorStoreVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10),
            ],
        };

        var storageModel = new JsonObject
        {
            ["id"] = "key",
            ["StringDataProp"] = null,
            ["NullableIntDataProp"] = null,
            ["NullableFloatVector"] = null
        };

        var sut = new CosmosNoSqlDynamicMapper(s_model, s_jsonSerializerOptions);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, includeVectors: true);

        // Assert
        Assert.Equal("key", dataModel["Key"]);
        Assert.Null(dataModel["StringDataProp"]);
        Assert.Null(dataModel["NullableIntDataProp"]);
        Assert.Null(dataModel["NullableFloatVector"]);
    }

    [Fact]
    public void MapFromStorageToDataModelThrowsForMissingKey()
    {
        // Arrange
        var sut = new CosmosNoSqlDynamicMapper(s_model, s_jsonSerializerOptions);

        var storageModel = new JsonObject();

        // Act & Assert
        var exception = Assert.Throws<InvalidOperationException>(
            () => sut.MapFromStorageToDataModel(storageModel, includeVectors: true));
    }

    [Fact]
    public void MapFromDataToStorageModelSkipsMissingProperties()
    {
        // Arrange
        VectorStoreCollectionDefinition definition = new()
        {
            Properties =
            [
                new VectorStoreKeyProperty("Key", typeof(string)),
                new VectorStoreDataProperty("StringDataProp", typeof(string)),
                new VectorStoreVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
            ],
        };

        var dataModel = new Dictionary<string, object?> { ["Key"] = "key" };
        var sut = new CosmosNoSqlDynamicMapper(s_model, s_jsonSerializerOptions);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal("key", (string?)storageModel["id"]);
        Assert.False(storageModel.ContainsKey("StringDataProp"));
        Assert.False(storageModel.ContainsKey("FloatVector"));
    }

    [Fact]
    public void MapFromStorageToDataModelSkipsMissingProperties()
    {
        // Arrange
        VectorStoreCollectionDefinition definition = new()
        {
            Properties =
            [
                new VectorStoreKeyProperty("Key", typeof(string)),
                new VectorStoreDataProperty("StringDataProp", typeof(string)),
                new VectorStoreVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
            ],
        };

        var storageModel = new JsonObject
        {
            ["id"] = "key"
        };

        var sut = new CosmosNoSqlDynamicMapper(s_model, s_jsonSerializerOptions);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, includeVectors: true);

        // Assert
        Assert.Equal("key", dataModel["Key"]);
        Assert.False(dataModel.ContainsKey("StringDataProp"));
        Assert.False(dataModel.ContainsKey("FloatVector"));
    }
}
