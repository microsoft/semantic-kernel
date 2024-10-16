// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Xunit;

namespace SemanticKernel.Connectors.AzureAISearch.UnitTests;

/// <summary>
/// Tests for the <see cref="AzureAISearchGenericDataModelMapper"/> class.
/// </summary>
public class AzureAISearchGenericDataModelMapperTests
{
    private static readonly VectorStoreRecordDefinition s_vectorStoreRecordDefinition = new()
    {
        Properties = new List<VectorStoreRecordProperty>
        {
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
            new VectorStoreRecordDataProperty("IntDataProp", typeof(int)),
            new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
            new VectorStoreRecordDataProperty("LongDataProp", typeof(long)),
            new VectorStoreRecordDataProperty("NullableLongDataProp", typeof(long?)),
            new VectorStoreRecordDataProperty("FloatDataProp", typeof(float)),
            new VectorStoreRecordDataProperty("NullableFloatDataProp", typeof(float?)),
            new VectorStoreRecordDataProperty("DoubleDataProp", typeof(double)),
            new VectorStoreRecordDataProperty("NullableDoubleDataProp", typeof(double?)),
            new VectorStoreRecordDataProperty("BoolDataProp", typeof(bool)),
            new VectorStoreRecordDataProperty("NullableBoolDataProp", typeof(bool?)),
            new VectorStoreRecordDataProperty("DateTimeOffsetDataProp", typeof(DateTimeOffset)),
            new VectorStoreRecordDataProperty("NullableDateTimeOffsetDataProp", typeof(DateTimeOffset?)),
            new VectorStoreRecordDataProperty("TagListDataProp", typeof(string[])),
            new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
            new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?)),
        },
    };

    private static readonly float[] s_vector1 = new float[] { 1.0f, 2.0f, 3.0f };
    private static readonly float[] s_vector2 = new float[] { 4.0f, 5.0f, 6.0f };
    private static readonly string[] s_taglist = new string[] { "tag1", "tag2" };

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange
        var sut = new AzureAISearchGenericDataModelMapper(s_vectorStoreRecordDefinition);
        var dataModel = new VectorStoreGenericDataModel<string>("key")
        {
            Data =
            {
                ["StringDataProp"] = "string",
                ["IntDataProp"] = 1,
                ["NullableIntDataProp"] = 2,
                ["LongDataProp"] = 3L,
                ["NullableLongDataProp"] = 4L,
                ["FloatDataProp"] = 5.0f,
                ["NullableFloatDataProp"] = 6.0f,
                ["DoubleDataProp"] = 7.0,
                ["NullableDoubleDataProp"] = 8.0,
                ["BoolDataProp"] = true,
                ["NullableBoolDataProp"] = false,
                ["DateTimeOffsetDataProp"] = new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero),
                ["NullableDateTimeOffsetDataProp"] = new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero),
                ["TagListDataProp"] = s_taglist,
            },
            Vectors =
            {
                ["FloatVector"] = new ReadOnlyMemory<float>(s_vector1),
                ["NullableFloatVector"] = new ReadOnlyMemory<float>(s_vector2),
            },
        };

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal("key", (string?)storageModel["Key"]);
        Assert.Equal("string", (string?)storageModel["StringDataProp"]);
        Assert.Equal(1, (int?)storageModel["IntDataProp"]);
        Assert.Equal(2, (int?)storageModel["NullableIntDataProp"]);
        Assert.Equal(3L, (long?)storageModel["LongDataProp"]);
        Assert.Equal(4L, (long?)storageModel["NullableLongDataProp"]);
        Assert.Equal(5.0f, (float?)storageModel["FloatDataProp"]);
        Assert.Equal(6.0f, (float?)storageModel["NullableFloatDataProp"]);
        Assert.Equal(7.0, (double?)storageModel["DoubleDataProp"]);
        Assert.Equal(8.0, (double?)storageModel["NullableDoubleDataProp"]);
        Assert.Equal(true, (bool?)storageModel["BoolDataProp"]);
        Assert.Equal(false, (bool?)storageModel["NullableBoolDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), (DateTimeOffset?)storageModel["DateTimeOffsetDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), (DateTimeOffset?)storageModel["NullableDateTimeOffsetDataProp"]);
        Assert.Equal(s_taglist, storageModel["TagListDataProp"]!.AsArray().Select(x => (string)x!).ToArray());
        Assert.Equal(s_vector1, storageModel["FloatVector"]!.AsArray().Select(x => (float)x!).ToArray());
        Assert.Equal(s_vector2, storageModel["NullableFloatVector"]!.AsArray().Select(x => (float)x!).ToArray());
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

        var sut = new AzureAISearchGenericDataModelMapper(vectorStoreRecordDefinition);

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
        var sut = new AzureAISearchGenericDataModelMapper(s_vectorStoreRecordDefinition);
        var storageModel = new JsonObject();
        storageModel["Key"] = "key";
        storageModel["StringDataProp"] = "string";
        storageModel["IntDataProp"] = 1;
        storageModel["NullableIntDataProp"] = 2;
        storageModel["LongDataProp"] = 3L;
        storageModel["NullableLongDataProp"] = 4L;
        storageModel["FloatDataProp"] = 5.0f;
        storageModel["NullableFloatDataProp"] = 6.0f;
        storageModel["DoubleDataProp"] = 7.0;
        storageModel["NullableDoubleDataProp"] = 8.0;
        storageModel["BoolDataProp"] = true;
        storageModel["NullableBoolDataProp"] = false;
        storageModel["DateTimeOffsetDataProp"] = new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero);
        storageModel["NullableDateTimeOffsetDataProp"] = new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero);
        storageModel["TagListDataProp"] = new JsonArray { "tag1", "tag2" };
        storageModel["FloatVector"] = new JsonArray { 1.0f, 2.0f, 3.0f };
        storageModel["NullableFloatVector"] = new JsonArray { 4.0f, 5.0f, 6.0f };

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

        // Assert
        Assert.Equal("key", dataModel.Key);
        Assert.Equal("string", dataModel.Data["StringDataProp"]);
        Assert.Equal(1, dataModel.Data["IntDataProp"]);
        Assert.Equal(2, dataModel.Data["NullableIntDataProp"]);
        Assert.Equal(3L, dataModel.Data["LongDataProp"]);
        Assert.Equal(4L, dataModel.Data["NullableLongDataProp"]);
        Assert.Equal(5.0f, dataModel.Data["FloatDataProp"]);
        Assert.Equal(6.0f, dataModel.Data["NullableFloatDataProp"]);
        Assert.Equal(7.0, dataModel.Data["DoubleDataProp"]);
        Assert.Equal(8.0, dataModel.Data["NullableDoubleDataProp"]);
        Assert.Equal(true, dataModel.Data["BoolDataProp"]);
        Assert.Equal(false, dataModel.Data["NullableBoolDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), dataModel.Data["DateTimeOffsetDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), dataModel.Data["NullableDateTimeOffsetDataProp"]);
        Assert.Equal(s_taglist, dataModel.Data["TagListDataProp"]);
        Assert.Equal(s_vector1, ((ReadOnlyMemory<float>)dataModel.Vectors["FloatVector"]!).ToArray());
        Assert.Equal(s_vector2, ((ReadOnlyMemory<float>)dataModel.Vectors["NullableFloatVector"]!)!.ToArray());
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

        var storageModel = new JsonObject();
        storageModel["Key"] = "key";
        storageModel["StringDataProp"] = null;
        storageModel["NullableIntDataProp"] = null;
        storageModel["NullableFloatVector"] = null;

        var sut = new AzureAISearchGenericDataModelMapper(vectorStoreRecordDefinition);

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
        var sut = new AzureAISearchGenericDataModelMapper(s_vectorStoreRecordDefinition);
        var storageModel = new JsonObject();

        // Act
        var exception = Assert.Throws<VectorStoreRecordMappingException>(() => sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true }));

        // Assert
        Assert.Equal("The key property 'Key' is missing from the record retrieved from storage.", exception.Message);
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
        var sut = new AzureAISearchGenericDataModelMapper(vectorStoreRecordDefinition);

        // Act
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal("key", (string?)storageModel["Key"]);
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

        var storageModel = new JsonObject();
        storageModel["Key"] = "key";

        var sut = new AzureAISearchGenericDataModelMapper(vectorStoreRecordDefinition);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

        // Assert
        Assert.Equal("key", dataModel.Key);
        Assert.False(dataModel.Data.ContainsKey("StringDataProp"));
        Assert.False(dataModel.Vectors.ContainsKey("FloatVector"));
    }
}
