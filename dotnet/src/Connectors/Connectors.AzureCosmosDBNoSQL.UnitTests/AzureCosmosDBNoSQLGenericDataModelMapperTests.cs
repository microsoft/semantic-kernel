// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBNoSQL.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBNoSQLGenericDataModelMapper"/> class.
/// </summary>
public sealed class AzureCosmosDBNoSQLGenericDataModelMapperTests
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = JsonSerializerOptions.Default;

    private static readonly VectorStoreRecordModel s_model = new AzureCosmosDBNoSqlVectorStoreModelBuilder()
        .Build(
            typeof(VectorStoreGenericDataModel<Guid>),
            new VectorStoreRecordDefinition
            {
                Properties = new List<VectorStoreRecordProperty>
                {
                    new VectorStoreRecordKeyProperty("Key", typeof(string)),
                    new VectorStoreRecordDataProperty("BoolDataProp", typeof(bool)),
                    new VectorStoreRecordDataProperty("NullableBoolDataProp", typeof(bool?)),
                    new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                    new VectorStoreRecordDataProperty("IntDataProp", typeof(int)),
                    new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
                    new VectorStoreRecordDataProperty("LongDataProp", typeof(long)),
                    new VectorStoreRecordDataProperty("NullableLongDataProp", typeof(long?)),
                    new VectorStoreRecordDataProperty("FloatDataProp", typeof(float)),
                    new VectorStoreRecordDataProperty("NullableFloatDataProp", typeof(float?)),
                    new VectorStoreRecordDataProperty("DoubleDataProp", typeof(double)),
                    new VectorStoreRecordDataProperty("NullableDoubleDataProp", typeof(double?)),
                    new VectorStoreRecordDataProperty("DateTimeOffsetDataProp", typeof(DateTimeOffset)),
                    new VectorStoreRecordDataProperty("NullableDateTimeOffsetDataProp", typeof(DateTimeOffset?)),
                    new VectorStoreRecordDataProperty("TagListDataProp", typeof(List<string>)),
        #if NET5_0_OR_GREATER
                    new VectorStoreRecordVectorProperty("HalfVector", typeof(ReadOnlyMemory<Half>)),
                    new VectorStoreRecordVectorProperty("NullableHalfVector", typeof(ReadOnlyMemory<Half>?)),
        #endif
                    new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
                    new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?)),
                    new VectorStoreRecordVectorProperty("ByteVector", typeof(ReadOnlyMemory<byte>)),
                    new VectorStoreRecordVectorProperty("NullableByteVector", typeof(ReadOnlyMemory<byte>?)),
                    new VectorStoreRecordVectorProperty("SByteVector", typeof(ReadOnlyMemory<sbyte>)),
                    new VectorStoreRecordVectorProperty("NullableSByteVector", typeof(ReadOnlyMemory<sbyte>?)),
                },
            });

#if NET5_0_OR_GREATER
    private static readonly Half[] s_halfVector = [(Half)1.0f, (Half)2.0f, (Half)3.0f];
#endif
    private static readonly float[] s_floatVector = [1.0f, 2.0f, 3.0f];
    private static readonly byte[] s_byteVector = [1, 2, 3];
    private static readonly sbyte[] s_sbyteVector = [1, 2, 3];
    private static readonly List<string> s_taglist = ["tag1", "tag2"];

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLGenericDataModelMapper(s_model, s_jsonSerializerOptions);

        var dataModel = new VectorStoreGenericDataModel<string>("key")
        {
            Data =
            {
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
            },
            Vectors =
            {
#if NET5_0_OR_GREATER
                ["HalfVector"] = new ReadOnlyMemory<Half>(s_halfVector),
                ["NullableHalfVector"] = new ReadOnlyMemory<Half>(s_halfVector),
#endif
                ["FloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
                ["NullableFloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
                ["ByteVector"] = new ReadOnlyMemory<byte>(s_byteVector),
                ["NullableByteVector"] = new ReadOnlyMemory<byte>(s_byteVector),
                ["SByteVector"] = new ReadOnlyMemory<sbyte>(s_sbyteVector),
                ["NullableSByteVector"] = new ReadOnlyMemory<sbyte>(s_sbyteVector)
            },
        };

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

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
#if NET5_0_OR_GREATER
        Assert.Equal(s_halfVector, storageModel["HalfVector"]!.AsArray().Select(l => (Half)(float)l!).ToArray());
        Assert.Equal(s_halfVector, storageModel["NullableHalfVector"]!.AsArray().Select(l => (Half)(float)l!).ToArray());
#endif
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
        VectorStoreRecordDefinition vectorStoreRecordDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
                new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?)),
            },
        };

        var dataModel = new VectorStoreGenericDataModel<string>("key")
        {
            Data =
            {
                ["StringDataProp"] = null,
                ["NullableIntDataProp"] = null,
            },
            Vectors =
            {
                ["NullableFloatVector"] = null,
            },
        };

        var sut = new AzureCosmosDBNoSQLGenericDataModelMapper(s_model, s_jsonSerializerOptions);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Null(storageModel["StringDataProp"]);
        Assert.Null(storageModel["NullableIntDataProp"]);
        Assert.Null(storageModel["NullableFloatVector"]);
    }

    [Fact]
    public void MapFromStorageToDataModelMapsAllSupportedTypes()
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLGenericDataModelMapper(s_model, s_jsonSerializerOptions);

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
#if NET5_0_OR_GREATER
            ["HalfVector"] = new JsonArray(s_halfVector.Select(l => (JsonValue)(float)l).ToArray()),
            ["NullableHalfVector"] = new JsonArray(s_halfVector.Select(l => (JsonValue)(float)l).ToArray()),
#endif
            ["FloatVector"] = new JsonArray(s_floatVector.Select(l => (JsonValue)l).ToArray()),
            ["NullableFloatVector"] = new JsonArray(s_floatVector.Select(l => (JsonValue)l).ToArray()),
            ["ByteVector"] = new JsonArray(s_byteVector.Select(l => (JsonValue)l).ToArray()),
            ["NullableByteVector"] = new JsonArray(s_byteVector.Select(l => (JsonValue)l).ToArray()),
            ["SByteVector"] = new JsonArray(s_sbyteVector.Select(l => (JsonValue)l).ToArray()),
            ["NullableSByteVector"] = new JsonArray(s_sbyteVector.Select(l => (JsonValue)l).ToArray())
        };

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

        // Assert
        Assert.Equal("key", dataModel.Key);
        Assert.Equal(true, dataModel.Data["BoolDataProp"]);
        Assert.Equal(false, dataModel.Data["NullableBoolDataProp"]);
        Assert.Equal("string", dataModel.Data["StringDataProp"]);
        Assert.Equal(1, dataModel.Data["IntDataProp"]);
        Assert.Equal(2, dataModel.Data["NullableIntDataProp"]);
        Assert.Equal(3L, dataModel.Data["LongDataProp"]);
        Assert.Equal(4L, dataModel.Data["NullableLongDataProp"]);
        Assert.Equal(5.0f, dataModel.Data["FloatDataProp"]);
        Assert.Equal(6.0f, dataModel.Data["NullableFloatDataProp"]);
        Assert.Equal(7.0, dataModel.Data["DoubleDataProp"]);
        Assert.Equal(8.0, dataModel.Data["NullableDoubleDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), dataModel.Data["DateTimeOffsetDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), dataModel.Data["NullableDateTimeOffsetDataProp"]);
        Assert.Equal(s_taglist, dataModel.Data["TagListDataProp"]);
#if NET5_0_OR_GREATER
        Assert.Equal(s_halfVector, ((ReadOnlyMemory<Half>)dataModel.Vectors["HalfVector"]!).ToArray());
        Assert.Equal(s_halfVector, ((ReadOnlyMemory<Half>)dataModel.Vectors["NullableHalfVector"]!)!.ToArray());
#endif
        Assert.Equal(s_floatVector, ((ReadOnlyMemory<float>)dataModel.Vectors["FloatVector"]!).ToArray());
        Assert.Equal(s_floatVector, ((ReadOnlyMemory<float>)dataModel.Vectors["NullableFloatVector"]!)!.ToArray());
        Assert.Equal(s_byteVector, ((ReadOnlyMemory<byte>)dataModel.Vectors["ByteVector"]!).ToArray());
        Assert.Equal(s_byteVector, ((ReadOnlyMemory<byte>)dataModel.Vectors["NullableByteVector"]!)!.ToArray());
        Assert.Equal(s_sbyteVector, ((ReadOnlyMemory<sbyte>)dataModel.Vectors["SByteVector"]!).ToArray());
        Assert.Equal(s_sbyteVector, ((ReadOnlyMemory<sbyte>)dataModel.Vectors["NullableSByteVector"]!)!.ToArray());
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
                new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
                new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?)),
            },
        };

        var storageModel = new JsonObject
        {
            ["id"] = "key",
            ["StringDataProp"] = null,
            ["NullableIntDataProp"] = null,
            ["NullableFloatVector"] = null
        };

        var sut = new AzureCosmosDBNoSQLGenericDataModelMapper(s_model, s_jsonSerializerOptions);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

        // Assert
        Assert.Equal("key", dataModel.Key);
        Assert.Null(dataModel.Data["StringDataProp"]);
        Assert.Null(dataModel.Data["NullableIntDataProp"]);
        Assert.Null(dataModel.Vectors["NullableFloatVector"]);
    }

    [Fact]
    public void MapFromStorageToDataModelThrowsForMissingKey()
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLGenericDataModelMapper(s_model, s_jsonSerializerOptions);

        var storageModel = new JsonObject();

        // Act & Assert
        var exception = Assert.Throws<VectorStoreRecordMappingException>(
            () => sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true }));
    }

    [Fact]
    public void MapFromDataToStorageModelSkipsMissingProperties()
    {
        // Arrange
        VectorStoreRecordDefinition vectorStoreRecordDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
            },
        };

        var dataModel = new VectorStoreGenericDataModel<string>("key");
        var sut = new AzureCosmosDBNoSQLGenericDataModelMapper(s_model, s_jsonSerializerOptions);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal("key", (string?)storageModel["id"]);
        Assert.False(storageModel.ContainsKey("StringDataProp"));
        Assert.False(storageModel.ContainsKey("FloatVector"));
    }

    [Fact]
    public void MapFromStorageToDataModelSkipsMissingProperties()
    {
        // Arrange
        VectorStoreRecordDefinition vectorStoreRecordDefinition = new()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
            },
        };

        var storageModel = new JsonObject
        {
            ["id"] = "key"
        };

        var sut = new AzureCosmosDBNoSQLGenericDataModelMapper(s_model, s_jsonSerializerOptions);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

        // Assert
        Assert.Equal("key", dataModel.Key);
        Assert.False(dataModel.Data.ContainsKey("StringDataProp"));
        Assert.False(dataModel.Vectors.ContainsKey("FloatVector"));
    }
}
