// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;
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

    private static readonly VectorStoreRecordKeyProperty s_keyProperty = new("Key", typeof(Guid));

    private static readonly List<VectorStoreRecordDataProperty> s_dataProperties = new()
    {
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
    };

    private static readonly List<VectorStoreRecordVectorProperty> s_vectorProperties = new()
    {
        new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
        new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?)),
        new VectorStoreRecordVectorProperty("DoubleVector", typeof(ReadOnlyMemory<double>)),
        new VectorStoreRecordVectorProperty("NullableDoubleVector", typeof(ReadOnlyMemory<double>?)),
    };

    private static readonly Dictionary<string, string> s_storagePropertyNames = s_dataProperties
        .Select(l => l.DataModelPropertyName)
        .Concat(s_vectorProperties.Select(l => l.DataModelPropertyName))
        .Concat([s_keyProperty.DataModelPropertyName])
        .ToDictionary(k => k, v => v);

    private static readonly float[] s_floatVector = [1.0f, 2.0f, 3.0f];
    private static readonly double[] s_doubleVector = [1.0f, 2.0f, 3.0f];
    private static readonly List<string> s_taglist = ["tag1", "tag2"];

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange
        var key = new Guid("55555555-5555-5555-5555-555555555555");
        var sut = new WeaviateGenericDataModelMapper(
            "Collection",
            s_keyProperty,
            s_dataProperties,
            s_vectorProperties,
            s_storagePropertyNames,
            s_jsonSerializerOptions);

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
        Assert.Equal("string", (string?)storageModel["properties"]?["StringDataProp"]);
        Assert.Equal(true, (bool?)storageModel["properties"]?["BoolDataProp"]);
        Assert.Equal(false, (bool?)storageModel["properties"]?["NullableBoolDataProp"]);
        Assert.Equal(1, (int?)storageModel["properties"]?["IntDataProp"]);
        Assert.Equal(2, (int?)storageModel["properties"]?["NullableIntDataProp"]);
        Assert.Equal(3L, (long?)storageModel["properties"]?["LongDataProp"]);
        Assert.Equal(4L, (long?)storageModel["properties"]?["NullableLongDataProp"]);
        Assert.Equal((short)5, (short?)storageModel["properties"]?["ShortDataProp"]);
        Assert.Equal((short)6, (short?)storageModel["properties"]?["NullableShortDataProp"]);
        Assert.Equal((byte)7, (byte?)storageModel["properties"]?["ByteDataProp"]);
        Assert.Equal((byte)8, (byte?)storageModel["properties"]?["NullableByteDataProp"]);
        Assert.Equal(9.0f, (float?)storageModel["properties"]?["FloatDataProp"]);
        Assert.Equal(10.0f, (float?)storageModel["properties"]?["NullableFloatDataProp"]);
        Assert.Equal(11.0, (double?)storageModel["properties"]?["DoubleDataProp"]);
        Assert.Equal(12.0, (double?)storageModel["properties"]?["NullableDoubleDataProp"]);
        Assert.Equal(13.99m, (decimal?)storageModel["properties"]?["DecimalDataProp"]);
        Assert.Equal(14.00m, (decimal?)storageModel["properties"]?["NullableDecimalDataProp"]);
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0), (DateTime?)storageModel["properties"]?["DateTimeDataProp"]);
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0), (DateTime?)storageModel["properties"]?["NullableDateTimeDataProp"]);
        Assert.Equal(new DateTimeOffset(2022, 1, 1, 0, 0, 0, TimeSpan.Zero), (DateTimeOffset?)storageModel["properties"]?["DateTimeOffsetDataProp"]);
        Assert.Equal(new DateTimeOffset(2022, 1, 1, 0, 0, 0, TimeSpan.Zero), (DateTimeOffset?)storageModel["properties"]?["NullableDateTimeOffsetDataProp"]);
        Assert.Equal(new Guid("11111111-1111-1111-1111-111111111111"), (Guid?)storageModel["properties"]?["GuidDataProp"]);
        Assert.Equal(new Guid("22222222-2222-2222-2222-222222222222"), (Guid?)storageModel["properties"]?["NullableGuidDataProp"]);
        Assert.Equal(s_taglist, storageModel["properties"]?["TagListDataProp"]!.AsArray().GetValues<string>().ToArray());
        Assert.Equal(s_floatVector, storageModel["vectors"]?["FloatVector"]!.AsArray().GetValues<float>().ToArray());
        Assert.Equal(s_floatVector, storageModel["vectors"]?["NullableFloatVector"]!.AsArray().GetValues<float>().ToArray());
        Assert.Equal(s_doubleVector, storageModel["vectors"]?["DoubleVector"]!.AsArray().GetValues<double>().ToArray());
        Assert.Equal(s_doubleVector, storageModel["vectors"]?["NullableDoubleVector"]!.AsArray().GetValues<double>().ToArray());
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
            new("NullableFloatVector", typeof(ReadOnlyMemory<float>?))
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

        var sut = new WeaviateGenericDataModelMapper(
            "Collection",
            keyProperty,
            dataProperties,
            vectorProperties,
            s_storagePropertyNames,
            s_jsonSerializerOptions);

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
        var sut = new WeaviateGenericDataModelMapper(
            "Collection",
            s_keyProperty,
            s_dataProperties,
            s_vectorProperties,
            s_storagePropertyNames,
            s_jsonSerializerOptions);

        var storageModel = new JsonObject
        {
            ["id"] = key,
            ["properties"] = new JsonObject
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
                ["TagListDataProp"] = new JsonArray(s_taglist.Select(l => (JsonValue)l).ToArray())
            },
            ["vectors"] = new JsonObject
            {
                ["FloatVector"] = new JsonArray(s_floatVector.Select(l => (JsonValue)l).ToArray()),
                ["NullableFloatVector"] = new JsonArray(s_floatVector.Select(l => (JsonValue)l).ToArray()),
                ["DoubleVector"] = new JsonArray(s_doubleVector.Select(l => (JsonValue)l).ToArray()),
                ["NullableDoubleVector"] = new JsonArray(s_doubleVector.Select(l => (JsonValue)l).ToArray()),
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
            new("NullableFloatVector", typeof(ReadOnlyMemory<float>?))
        };

        var storageModel = new JsonObject
        {
            ["id"] = key,
            ["properties"] = new JsonObject
            {
                ["StringDataProp"] = null,
                ["NullableIntDataProp"] = null,
            },
            ["vectors"] = new JsonObject
            {
                ["NullableFloatVector"] = null
            }
        };

        var sut = new WeaviateGenericDataModelMapper(
            "Collection",
            s_keyProperty,
            s_dataProperties,
            s_vectorProperties,
            s_storagePropertyNames,
            s_jsonSerializerOptions);

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
        var sut = new WeaviateGenericDataModelMapper(
            "Collection",
            s_keyProperty,
            s_dataProperties,
            s_vectorProperties,
            s_storagePropertyNames,
            s_jsonSerializerOptions);

        var storageModel = new JsonObject();

        // Act & Assert
        var exception = Assert.Throws<VectorStoreRecordMappingException>(
            () => sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true }));
    }

    [Fact]
    public void MapFromDataToStorageModelSkipsMissingProperties()
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
            new("FloatVector", typeof(ReadOnlyMemory<float>))
        };

        var dataModel = new VectorStoreGenericDataModel<Guid>(key);
        var sut = new WeaviateGenericDataModelMapper(
            "Collection",
            keyProperty,
            dataProperties,
            vectorProperties,
            s_storagePropertyNames,
            s_jsonSerializerOptions);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal(key, (Guid?)storageModel["id"]);
        Assert.False(storageModel.ContainsKey("StringDataProp"));
        Assert.False(storageModel.ContainsKey("FloatVector"));
    }

    [Fact]
    public void MapFromStorageToDataModelSkipsMissingProperties()
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
            new("FloatVector", typeof(ReadOnlyMemory<float>))
        };

        var sut = new WeaviateGenericDataModelMapper(
            "Collection",
            keyProperty,
            dataProperties,
            vectorProperties,
            s_storagePropertyNames,
            s_jsonSerializerOptions);

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
