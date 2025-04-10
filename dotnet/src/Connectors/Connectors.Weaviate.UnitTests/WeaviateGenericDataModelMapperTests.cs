// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

/// <summary>
/// Unit tests for <see cref="WeaviateGenericDataModelMapper"/> class.
/// </summary>
public sealed class WeaviateGenericDataModelMapperTests
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Converters =
        {
            new WeaviateDateTimeOffsetConverter(),
            new WeaviateNullableDateTimeOffsetConverter()
        }
    };

    private static readonly VectorStoreRecordModel s_model = new WeaviateModelBuilder()
        .Build(
            typeof(VectorStoreGenericDataModel<Guid>),
            new VectorStoreRecordDefinition
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty("Key", typeof(Guid)),

                    new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                    new VectorStoreRecordDataProperty("BoolDataProp", typeof(bool)),
                    new VectorStoreRecordDataProperty("NullableBoolDataProp", typeof(bool?)),
                    new VectorStoreRecordDataProperty("IntDataProp", typeof(int)),
                    new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
                    new VectorStoreRecordDataProperty("LongDataProp", typeof(long)),
                    new VectorStoreRecordDataProperty("NullableLongDataProp", typeof(long?)),
                    new VectorStoreRecordDataProperty("ShortDataProp", typeof(short)),
                    new VectorStoreRecordDataProperty("NullableShortDataProp", typeof(short?)),
                    new VectorStoreRecordDataProperty("ByteDataProp", typeof(byte)),
                    new VectorStoreRecordDataProperty("NullableByteDataProp", typeof(byte?)),
                    new VectorStoreRecordDataProperty("FloatDataProp", typeof(float)),
                    new VectorStoreRecordDataProperty("NullableFloatDataProp", typeof(float?)),
                    new VectorStoreRecordDataProperty("DoubleDataProp", typeof(double)),
                    new VectorStoreRecordDataProperty("NullableDoubleDataProp", typeof(double?)),
                    new VectorStoreRecordDataProperty("DecimalDataProp", typeof(decimal)),
                    new VectorStoreRecordDataProperty("NullableDecimalDataProp", typeof(decimal?)),
                    new VectorStoreRecordDataProperty("DateTimeDataProp", typeof(DateTime)),
                    new VectorStoreRecordDataProperty("NullableDateTimeDataProp", typeof(DateTime?)),
                    new VectorStoreRecordDataProperty("DateTimeOffsetDataProp", typeof(DateTimeOffset)),
                    new VectorStoreRecordDataProperty("NullableDateTimeOffsetDataProp", typeof(DateTimeOffset?)),
                    new VectorStoreRecordDataProperty("GuidDataProp", typeof(Guid)),
                    new VectorStoreRecordDataProperty("NullableGuidDataProp", typeof(Guid?)),
                    new VectorStoreRecordDataProperty("TagListDataProp", typeof(List<string>)),

                    new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
                    new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10),
                    new VectorStoreRecordVectorProperty("DoubleVector", typeof(ReadOnlyMemory<double>), 10),
                    new VectorStoreRecordVectorProperty("NullableDoubleVector", typeof(ReadOnlyMemory<double>?), 10)
                ]
            },
            s_jsonSerializerOptions);

    private static readonly float[] s_floatVector = [1.0f, 2.0f, 3.0f];
    private static readonly double[] s_doubleVector = [1.0f, 2.0f, 3.0f];
    private static readonly List<string> s_taglist = ["tag1", "tag2"];

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange
        var key = new Guid("55555555-5555-5555-5555-555555555555");
        var sut = new WeaviateGenericDataModelMapper("Collection", s_model, s_jsonSerializerOptions);

        var dataModel = new VectorStoreGenericDataModel<Guid>(key)
        {
            Data =
            {
                ["StringDataProp"] = "string",
                ["BoolDataProp"] = true,
                ["NullableBoolDataProp"] = false,
                ["IntDataProp"] = 1,
                ["NullableIntDataProp"] = 2,
                ["LongDataProp"] = 3L,
                ["NullableLongDataProp"] = 4L,
                ["ShortDataProp"] = (short)5,
                ["NullableShortDataProp"] = (short)6,
                ["ByteDataProp"] = (byte)7,
                ["NullableByteDataProp"] = (byte)8,
                ["FloatDataProp"] = 9.0f,
                ["NullableFloatDataProp"] = 10.0f,
                ["DoubleDataProp"] = 11.0,
                ["NullableDoubleDataProp"] = 12.0,
                ["DecimalDataProp"] = 13.99m,
                ["NullableDecimalDataProp"] = 14.00m,
                ["DateTimeDataProp"] = new DateTime(2021, 1, 1),
                ["NullableDateTimeDataProp"] = new DateTime(2021, 1, 1),
                ["DateTimeOffsetDataProp"] = new DateTimeOffset(2022, 1, 1, 0, 0, 0, TimeSpan.Zero),
                ["NullableDateTimeOffsetDataProp"] = new DateTimeOffset(2022, 1, 1, 0, 0, 0, TimeSpan.Zero),
                ["GuidDataProp"] = new Guid("11111111-1111-1111-1111-111111111111"),
                ["NullableGuidDataProp"] = new Guid("22222222-2222-2222-2222-222222222222"),
                ["TagListDataProp"] = s_taglist
            },
            Vectors =
            {
                ["FloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
                ["NullableFloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
                ["DoubleVector"] = new ReadOnlyMemory<double>(s_doubleVector),
                ["NullableDoubleVector"] = new ReadOnlyMemory<double>(s_doubleVector),
            }
        };

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal(key, (Guid?)storageModel["id"]);
        Assert.Equal("Collection", (string?)storageModel["class"]);
        Assert.Equal("string", (string?)storageModel["properties"]?["stringDataProp"]);
        Assert.Equal(true, (bool?)storageModel["properties"]?["boolDataProp"]);
        Assert.Equal(false, (bool?)storageModel["properties"]?["nullableBoolDataProp"]);
        Assert.Equal(1, (int?)storageModel["properties"]?["intDataProp"]);
        Assert.Equal(2, (int?)storageModel["properties"]?["nullableIntDataProp"]);
        Assert.Equal(3L, (long?)storageModel["properties"]?["longDataProp"]);
        Assert.Equal(4L, (long?)storageModel["properties"]?["nullableLongDataProp"]);
        Assert.Equal((short)5, (short?)storageModel["properties"]?["shortDataProp"]);
        Assert.Equal((short)6, (short?)storageModel["properties"]?["nullableShortDataProp"]);
        Assert.Equal((byte)7, (byte?)storageModel["properties"]?["byteDataProp"]);
        Assert.Equal((byte)8, (byte?)storageModel["properties"]?["nullableByteDataProp"]);
        Assert.Equal(9.0f, (float?)storageModel["properties"]?["floatDataProp"]);
        Assert.Equal(10.0f, (float?)storageModel["properties"]?["nullableFloatDataProp"]);
        Assert.Equal(11.0, (double?)storageModel["properties"]?["doubleDataProp"]);
        Assert.Equal(12.0, (double?)storageModel["properties"]?["nullableDoubleDataProp"]);
        Assert.Equal(13.99m, (decimal?)storageModel["properties"]?["decimalDataProp"]);
        Assert.Equal(14.00m, (decimal?)storageModel["properties"]?["nullableDecimalDataProp"]);
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0), (DateTime?)storageModel["properties"]?["dateTimeDataProp"]);
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0), (DateTime?)storageModel["properties"]?["nullableDateTimeDataProp"]);
        Assert.Equal(new DateTimeOffset(2022, 1, 1, 0, 0, 0, TimeSpan.Zero), (DateTimeOffset?)storageModel["properties"]?["dateTimeOffsetDataProp"]);
        Assert.Equal(new DateTimeOffset(2022, 1, 1, 0, 0, 0, TimeSpan.Zero), (DateTimeOffset?)storageModel["properties"]?["nullableDateTimeOffsetDataProp"]);
        Assert.Equal(new Guid("11111111-1111-1111-1111-111111111111"), (Guid?)storageModel["properties"]?["guidDataProp"]);
        Assert.Equal(new Guid("22222222-2222-2222-2222-222222222222"), (Guid?)storageModel["properties"]?["nullableGuidDataProp"]);
        Assert.Equal(s_taglist, storageModel["properties"]?["tagListDataProp"]!.AsArray().GetValues<string>().ToArray());
        Assert.Equal(s_floatVector, storageModel["vectors"]?["floatVector"]!.AsArray().GetValues<float>().ToArray());
        Assert.Equal(s_floatVector, storageModel["vectors"]?["nullableFloatVector"]!.AsArray().GetValues<float>().ToArray());
        Assert.Equal(s_doubleVector, storageModel["vectors"]?["doubleVector"]!.AsArray().GetValues<double>().ToArray());
        Assert.Equal(s_doubleVector, storageModel["vectors"]?["nullableDoubleVector"]!.AsArray().GetValues<double>().ToArray());
    }

    [Fact]
    public void MapFromDataToStorageModelMapsNullValues()
    {
        // Arrange
        var key = new Guid("55555555-5555-5555-5555-555555555555");
        var keyProperty = new VectorStoreRecordKeyProperty("Key", typeof(Guid));

        var dataProperties = new List<VectorStoreRecordDataProperty>
        {
            new("StringDataProp", typeof(string)),
            new("NullableIntDataProp", typeof(int?)),
        };

        var vectorProperties = new List<VectorStoreRecordVectorProperty>
        {
            new("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10)
        };

        var dataModel = new VectorStoreGenericDataModel<Guid>(key)
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

        var sut = new WeaviateGenericDataModelMapper("Collection", s_model, s_jsonSerializerOptions);

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
        var key = new Guid("55555555-5555-5555-5555-555555555555");
        var sut = new WeaviateGenericDataModelMapper("Collection", s_model, s_jsonSerializerOptions);

        var storageModel = new JsonObject
        {
            ["id"] = key,
            ["properties"] = new JsonObject
            {
                ["stringDataProp"] = "string",
                ["boolDataProp"] = true,
                ["nullableBoolDataProp"] = false,
                ["intDataProp"] = 1,
                ["nullableIntDataProp"] = 2,
                ["longDataProp"] = 3L,
                ["nullableLongDataProp"] = 4L,
                ["shortDataProp"] = (short)5,
                ["nullableShortDataProp"] = (short)6,
                ["byteDataProp"] = (byte)7,
                ["nullableByteDataProp"] = (byte)8,
                ["floatDataProp"] = 9.0f,
                ["nullableFloatDataProp"] = 10.0f,
                ["doubleDataProp"] = 11.0,
                ["nullableDoubleDataProp"] = 12.0,
                ["decimalDataProp"] = 13.99m,
                ["nullableDecimalDataProp"] = 14.00m,
                ["dateTimeDataProp"] = new DateTime(2021, 1, 1),
                ["nullableDateTimeDataProp"] = new DateTime(2021, 1, 1),
                ["dateTimeOffsetDataProp"] = new DateTimeOffset(2022, 1, 1, 0, 0, 0, TimeSpan.Zero),
                ["nullableDateTimeOffsetDataProp"] = new DateTimeOffset(2022, 1, 1, 0, 0, 0, TimeSpan.Zero),
                ["guidDataProp"] = new Guid("11111111-1111-1111-1111-111111111111"),
                ["nullableGuidDataProp"] = new Guid("22222222-2222-2222-2222-222222222222"),
                ["tagListDataProp"] = new JsonArray(s_taglist.Select(l => (JsonValue)l).ToArray())
            },
            ["vectors"] = new JsonObject
            {
                ["floatVector"] = new JsonArray(s_floatVector.Select(l => (JsonValue)l).ToArray()),
                ["nullableFloatVector"] = new JsonArray(s_floatVector.Select(l => (JsonValue)l).ToArray()),
                ["doubleVector"] = new JsonArray(s_doubleVector.Select(l => (JsonValue)l).ToArray()),
                ["nullableDoubleVector"] = new JsonArray(s_doubleVector.Select(l => (JsonValue)l).ToArray()),
            }
        };

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

        // Assert
        Assert.Equal(key, dataModel.Key);
        Assert.Equal("string", dataModel.Data["StringDataProp"]);
        Assert.Equal(true, dataModel.Data["BoolDataProp"]);
        Assert.Equal(false, dataModel.Data["NullableBoolDataProp"]);
        Assert.Equal(1, dataModel.Data["IntDataProp"]);
        Assert.Equal(2, dataModel.Data["NullableIntDataProp"]);
        Assert.Equal(3L, dataModel.Data["LongDataProp"]);
        Assert.Equal(4L, dataModel.Data["NullableLongDataProp"]);
        Assert.Equal((short)5, dataModel.Data["ShortDataProp"]);
        Assert.Equal((short)6, dataModel.Data["NullableShortDataProp"]);
        Assert.Equal((byte)7, dataModel.Data["ByteDataProp"]);
        Assert.Equal((byte)8, dataModel.Data["NullableByteDataProp"]);
        Assert.Equal(9.0f, dataModel.Data["FloatDataProp"]);
        Assert.Equal(10.0f, dataModel.Data["NullableFloatDataProp"]);
        Assert.Equal(11.0, dataModel.Data["DoubleDataProp"]);
        Assert.Equal(12.0, dataModel.Data["NullableDoubleDataProp"]);
        Assert.Equal(13.99m, dataModel.Data["DecimalDataProp"]);
        Assert.Equal(14.00m, dataModel.Data["NullableDecimalDataProp"]);
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0), dataModel.Data["DateTimeDataProp"]);
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0), dataModel.Data["NullableDateTimeDataProp"]);
        Assert.Equal(new DateTimeOffset(2022, 1, 1, 0, 0, 0, TimeSpan.Zero), dataModel.Data["DateTimeOffsetDataProp"]);
        Assert.Equal(new DateTimeOffset(2022, 1, 1, 0, 0, 0, TimeSpan.Zero), dataModel.Data["NullableDateTimeOffsetDataProp"]);
        Assert.Equal(new Guid("11111111-1111-1111-1111-111111111111"), dataModel.Data["GuidDataProp"]);
        Assert.Equal(new Guid("22222222-2222-2222-2222-222222222222"), dataModel.Data["NullableGuidDataProp"]);
        Assert.Equal(s_taglist, dataModel.Data["TagListDataProp"]);
        Assert.Equal(s_floatVector, ((ReadOnlyMemory<float>)dataModel.Vectors["FloatVector"]!).ToArray());
        Assert.Equal(s_floatVector, ((ReadOnlyMemory<float>)dataModel.Vectors["NullableFloatVector"]!)!.ToArray());
        Assert.Equal(s_doubleVector, ((ReadOnlyMemory<double>)dataModel.Vectors["DoubleVector"]!).ToArray());
        Assert.Equal(s_doubleVector, ((ReadOnlyMemory<double>)dataModel.Vectors["NullableDoubleVector"]!)!.ToArray());
    }

    [Fact]
    public void MapFromStorageToDataModelMapsNullValues()
    {
        // Arrange
        var key = new Guid("55555555-5555-5555-5555-555555555555");
        var keyProperty = new VectorStoreRecordKeyProperty("Key", typeof(Guid));

        var dataProperties = new List<VectorStoreRecordDataProperty>
        {
            new("StringDataProp", typeof(string)),
            new("NullableIntDataProp", typeof(int?)),
        };

        var vectorProperties = new List<VectorStoreRecordVectorProperty>
        {
            new("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10)
        };

        var storageModel = new JsonObject
        {
            ["id"] = key,
            ["properties"] = new JsonObject
            {
                ["stringDataProp"] = null,
                ["nullableIntDataProp"] = null,
            },
            ["vectors"] = new JsonObject
            {
                ["nullableFloatVector"] = null
            }
        };

        var sut = new WeaviateGenericDataModelMapper("Collection", s_model, s_jsonSerializerOptions);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

        // Assert
        Assert.Equal(key, dataModel.Key);
        Assert.Null(dataModel.Data["StringDataProp"]);
        Assert.Null(dataModel.Data["NullableIntDataProp"]);
        Assert.Null(dataModel.Vectors["NullableFloatVector"]);
    }

    [Fact]
    public void MapFromStorageToDataModelThrowsForMissingKey()
    {
        // Arrange
        var sut = new WeaviateGenericDataModelMapper("Collection", s_model, s_jsonSerializerOptions);

        var storageModel = new JsonObject();

        // Act & Assert
        var exception = Assert.Throws<VectorStoreRecordMappingException>(
            () => sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true }));
    }

    [Fact]
    public void MapFromDataToStorageModelSkipsMissingProperties()
    {
        // Arrange
        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty("Key", typeof(Guid)),
                new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10)
            ]
        };

        var model = new WeaviateModelBuilder().Build(typeof(VectorStoreGenericDataModel<Guid>), recordDefinition, s_jsonSerializerOptions);

        var key = new Guid("55555555-5555-5555-5555-555555555555");

        var record = new VectorStoreGenericDataModel<Guid>(key);
        var sut = new WeaviateGenericDataModelMapper("Collection", model, s_jsonSerializerOptions);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(record);

        // Assert
        Assert.Equal(key, (Guid?)storageModel["id"]);
        Assert.False(storageModel.ContainsKey("StringDataProp"));
        Assert.False(storageModel.ContainsKey("FloatVector"));
    }

    [Fact]
    public void MapFromStorageToDataModelSkipsMissingProperties()
    {
        // Arrange
        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty("Key", typeof(Guid)),
                new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
                new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
                new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10)
            ]
        };

        var model = new WeaviateModelBuilder().Build(typeof(VectorStoreGenericDataModel<Guid>), recordDefinition, s_jsonSerializerOptions);

        var key = new Guid("55555555-5555-5555-5555-555555555555");

        var sut = new WeaviateGenericDataModelMapper("Collection", model, s_jsonSerializerOptions);

        var storageModel = new JsonObject
        {
            ["id"] = key
        };

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

        // Assert
        Assert.Equal(key, dataModel.Key);
        Assert.False(dataModel.Data.ContainsKey("StringDataProp"));
        Assert.False(dataModel.Vectors.ContainsKey("FloatVector"));
    }
}
