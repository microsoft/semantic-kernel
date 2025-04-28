// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Bson;
using Xunit;

namespace SemanticKernel.Connectors.MongoDB.UnitTests;

/// <summary>
/// Unit tests for <see cref="MongoDBDynamicDataModelMapper"/> class.
/// </summary>
public sealed class MongoDBDynamicDataModelMapperTests
{
    private static readonly VectorStoreRecordModel s_model = BuildModel(
    [
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
        new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
        new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10),
        new VectorStoreRecordVectorProperty("DoubleVector", typeof(ReadOnlyMemory<double>), 10),
        new VectorStoreRecordVectorProperty("NullableDoubleVector", typeof(ReadOnlyMemory<double>?), 10)
    ]);

    private static readonly float[] s_floatVector = [1.0f, 2.0f, 3.0f];
    private static readonly double[] s_doubleVector = [1.0f, 2.0f, 3.0f];
    private static readonly List<string> s_taglist = ["tag1", "tag2"];

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange
        var sut = new MongoDBDynamicDataModelMapper(s_model);
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
            ["DecimalDataProp"] = 9.0m,
            ["NullableDecimalDataProp"] = 10.0m,
            ["DateTimeDataProp"] = new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(),
            ["NullableDateTimeDataProp"] = new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(),
            ["TagListDataProp"] = s_taglist,

            ["FloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
            ["NullableFloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
            ["DoubleVector"] = new ReadOnlyMemory<double>(s_doubleVector),
            ["NullableDoubleVector"] = new ReadOnlyMemory<double>(s_doubleVector),
        };

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel, generatedEmbeddings: null);

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
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
            new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
            new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10)
        ]);

        var dataModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",
            ["StringDataProp"] = null,
            ["NullableIntDataProp"] = null,
            ["NullableFloatVector"] = null
        };

        var sut = new MongoDBDynamicDataModelMapper(model);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel, generatedEmbeddings: null);

        // Assert
        Assert.Equal(BsonNull.Value, storageModel["StringDataProp"]);
        Assert.Equal(BsonNull.Value, storageModel["NullableIntDataProp"]);
        Assert.Empty(storageModel["NullableFloatVector"].AsBsonArray);
    }

    [Fact]
    public void MapFromStorageToDataModelMapsAllSupportedTypes()
    {
        // Arrange
        var sut = new MongoDBDynamicDataModelMapper(s_model);
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
        Assert.Equal(9.0m, dataModel["DecimalDataProp"]);
        Assert.Equal(10.0m, dataModel["NullableDecimalDataProp"]);
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(), dataModel["DateTimeDataProp"]);
        Assert.Equal(new DateTime(2021, 1, 1, 0, 0, 0).ToUniversalTime(), dataModel["NullableDateTimeDataProp"]);
        Assert.Equal(s_taglist, dataModel["TagListDataProp"]);
        Assert.Equal(s_floatVector, ((ReadOnlyMemory<float>)dataModel["FloatVector"]!).ToArray());
        Assert.Equal(s_floatVector, ((ReadOnlyMemory<float>)dataModel["NullableFloatVector"]!)!.ToArray());
        Assert.Equal(s_doubleVector, ((ReadOnlyMemory<double>)dataModel["DoubleVector"]!).ToArray());
        Assert.Equal(s_doubleVector, ((ReadOnlyMemory<double>)dataModel["NullableDoubleVector"]!)!.ToArray());
    }

    [Fact]
    public void MapFromStorageToDataModelMapsNullValues()
    {
        // Arrange
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
            new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
            new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10)
        ]);

        var storageModel = new BsonDocument
        {
            ["_id"] = "key",
            ["StringDataProp"] = BsonNull.Value,
            ["NullableIntDataProp"] = BsonNull.Value,
            ["NullableFloatVector"] = BsonNull.Value
        };

        var sut = new MongoDBDynamicDataModelMapper(model);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

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
        var sut = new MongoDBDynamicDataModelMapper(s_model);
        var storageModel = new BsonDocument();

        // Act & Assert
        var exception = Assert.Throws<VectorStoreRecordMappingException>(
            () => sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true }));
    }

    [Fact]
    public void MapFromDataToStorageModelSkipsMissingProperties()
    {
        // Arrange
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
            new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
        ]);

        var dataModel = new Dictionary<string, object?> { ["Key"] = "key" };
        var sut = new MongoDBDynamicDataModelMapper(model);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel, generatedEmbeddings: null);

        // Assert
        Assert.Equal("key", (string?)storageModel["_id"]);
        Assert.False(storageModel.Contains("StringDataProp"));
        Assert.False(storageModel.Contains("FloatVector"));
    }

    [Fact]
    public void MapFromStorageToDataModelSkipsMissingProperties()
    {
        // Arrange
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
            new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
        ]);

        var storageModel = new BsonDocument
        {
            ["_id"] = "key"
        };

        var sut = new MongoDBDynamicDataModelMapper(model);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

        // Assert
        Assert.Equal("key", dataModel["Key"]);
        Assert.False(dataModel.ContainsKey("StringDataProp"));
        Assert.False(dataModel.ContainsKey("FloatVector"));
    }

    private static VectorStoreRecordModel BuildModel(IReadOnlyList<VectorStoreRecordProperty> properties)
        => new MongoDBModelBuilder().Build(typeof(Dictionary<string, object?>), new() { Properties = properties }, defaultEmbeddingGenerator: null);
}
