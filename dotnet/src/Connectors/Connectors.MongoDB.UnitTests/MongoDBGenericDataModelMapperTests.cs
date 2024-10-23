// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Bson;
using Xunit;

namespace SemanticKernel.Connectors.MongoDB.UnitTests;

/// <summary>
/// Unit tests for <see cref="MongoDBGenericDataModelMapper"/> class.
/// </summary>
public sealed class MongoDBGenericDataModelMapperTests
{
    private static readonly VectorStoreRecordDefinition s_vectorStoreRecordDefinition = new()
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
            new VectorStoreRecordDataProperty("DecimalDataProp", typeof(decimal)),
            new VectorStoreRecordDataProperty("NullableDecimalDataProp", typeof(decimal?)),
            new VectorStoreRecordDataProperty("DateTimeDataProp", typeof(DateTime)),
            new VectorStoreRecordDataProperty("NullableDateTimeDataProp", typeof(DateTime?)),
            new VectorStoreRecordDataProperty("TagListDataProp", typeof(List<string>)),
            new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
            new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?)),
            new VectorStoreRecordVectorProperty("DoubleVector", typeof(ReadOnlyMemory<double>)),
            new VectorStoreRecordVectorProperty("NullableDoubleVector", typeof(ReadOnlyMemory<double>?)),
        },
    };

    private static readonly float[] s_floatVector = [1.0f, 2.0f, 3.0f];
    private static readonly double[] s_doubleVector = [1.0f, 2.0f, 3.0f];
    private static readonly List<string> s_taglist = ["tag1", "tag2"];

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange
        var sut = new MongoDBGenericDataModelMapper(s_vectorStoreRecordDefinition);
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
                ["DecimalDataProp"] = 9.0m,
                ["NullableDecimalDataProp"] = 10.0m,
                ["DateTimeDataProp"] = new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(),
                ["NullableDateTimeDataProp"] = new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(),
                ["TagListDataProp"] = s_taglist,
            },
            Vectors =
            {
                ["FloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
                ["NullableFloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
                ["DoubleVector"] = new ReadOnlyMemory<double>(s_doubleVector),
                ["NullableDoubleVector"] = new ReadOnlyMemory<double>(s_doubleVector),
            },
        };

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal("key", storageModel["_id"]);
        Assert.Equal(true, (bool?)storageModel["BoolDataProp"]);
        Assert.Equal(false, (bool?)storageModel["NullableBoolDataProp"]);
        Assert.Equal("string", (string?)storageModel["StringDataProp"]);
        Assert.Equal(1, (int?)storageModel["IntDataProp"]);
        Assert.Equal(2, (int?)storageModel["NullableIntDataProp"]);
        Assert.Equal(3L, (long?)storageModel["LongDataProp"]);
        Assert.Equal(4L, (long?)storageModel["NullableLongDataProp"]);
        Assert.Equal(5.0f, (float?)storageModel["FloatDataProp"].AsDouble);
        Assert.Equal(6.0f, (float?)storageModel["NullableFloatDataProp"].AsNullableDouble);
        Assert.Equal(7.0, (double?)storageModel["DoubleDataProp"]);
        Assert.Equal(8.0, (double?)storageModel["NullableDoubleDataProp"]);
        Assert.Equal(9.0m, (decimal?)storageModel["DecimalDataProp"]);
        Assert.Equal(10.0m, (decimal?)storageModel["NullableDecimalDataProp"]);
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(), storageModel["DateTimeDataProp"].ToUniversalTime());
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(), storageModel["NullableDateTimeDataProp"].ToUniversalTime());
        Assert.Equal(s_taglist, storageModel["TagListDataProp"]!.AsBsonArray.Select(x => (string)x!).ToArray());
        Assert.Equal(s_floatVector, storageModel["FloatVector"]!.AsBsonArray.Select(x => (float)x.AsDouble!).ToArray());
        Assert.Equal(s_floatVector, storageModel["NullableFloatVector"]!.AsBsonArray.Select(x => (float)x.AsNullableDouble!).ToArray());
        Assert.Equal(s_doubleVector, storageModel["DoubleVector"]!.AsBsonArray.Select(x => (double)x!).ToArray());
        Assert.Equal(s_doubleVector, storageModel["NullableDoubleVector"]!.AsBsonArray.Select(x => (double)x!).ToArray());
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

        var sut = new MongoDBGenericDataModelMapper(vectorStoreRecordDefinition);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal(BsonNull.Value, storageModel["StringDataProp"]);
        Assert.Equal(BsonNull.Value, storageModel["NullableIntDataProp"]);
        Assert.Empty(storageModel["NullableFloatVector"].AsBsonArray);
    }

    [Fact]
    public void MapFromStorageToDataModelMapsAllSupportedTypes()
    {
        // Arrange
        var sut = new MongoDBGenericDataModelMapper(s_vectorStoreRecordDefinition);
        var storageModel = new BsonDocument
        {
            ["_id"] = "key",
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
            ["DecimalDataProp"] = 9.0m,
            ["NullableDecimalDataProp"] = 10.0m,
            ["DateTimeDataProp"] = new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(),
            ["NullableDateTimeDataProp"] = new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(),
            ["TagListDataProp"] = BsonArray.Create(s_taglist),
            ["FloatVector"] = BsonArray.Create(s_floatVector),
            ["NullableFloatVector"] = BsonArray.Create(s_floatVector),
            ["DoubleVector"] = BsonArray.Create(s_doubleVector),
            ["NullableDoubleVector"] = BsonArray.Create(s_doubleVector)
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
        Assert.Equal(9.0m, dataModel.Data["DecimalDataProp"]);
        Assert.Equal(10.0m, dataModel.Data["NullableDecimalDataProp"]);
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(), dataModel.Data["DateTimeDataProp"]);
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(), dataModel.Data["NullableDateTimeDataProp"]);
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

        var storageModel = new BsonDocument
        {
            ["_id"] = "key",
            ["StringDataProp"] = BsonNull.Value,
            ["NullableIntDataProp"] = BsonNull.Value,
            ["NullableFloatVector"] = BsonNull.Value
        };

        var sut = new MongoDBGenericDataModelMapper(vectorStoreRecordDefinition);

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
        var sut = new MongoDBGenericDataModelMapper(s_vectorStoreRecordDefinition);
        var storageModel = new BsonDocument();

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
        var sut = new MongoDBGenericDataModelMapper(vectorStoreRecordDefinition);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal("key", (string?)storageModel["_id"]);
        Assert.False(storageModel.Contains("StringDataProp"));
        Assert.False(storageModel.Contains("FloatVector"));
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

        var storageModel = new BsonDocument
        {
            ["_id"] = "key"
        };

        var sut = new MongoDBGenericDataModelMapper(vectorStoreRecordDefinition);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

        // Assert
        Assert.Equal("key", dataModel.Key);
        Assert.False(dataModel.Data.ContainsKey("StringDataProp"));
        Assert.False(dataModel.Vectors.ContainsKey("FloatVector"));
    }
}
