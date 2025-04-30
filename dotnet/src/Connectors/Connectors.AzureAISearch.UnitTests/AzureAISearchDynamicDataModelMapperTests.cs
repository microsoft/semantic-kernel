// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Xunit;

namespace SemanticKernel.Connectors.AzureAISearch.UnitTests;

/// <summary>
/// Tests for the <see cref="AzureAISearchDynamicDataModelMapper"/> class.
/// </summary>
public class AzureAISearchDynamicDataModelMapperTests
{
    private static readonly VectorStoreRecordModel s_model = BuildModel(
    [
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
        new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
        new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10),
    ]);

    private static readonly float[] s_vector1 = [1.0f, 2.0f, 3.0f];
    private static readonly float[] s_vector2 = [4.0f, 5.0f, 6.0f];
    private static readonly string[] s_taglist = ["tag1", "tag2"];

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange
        var sut = new AzureAISearchDynamicDataModelMapper(s_model);
        var dataModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",

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

            ["FloatVector"] = new ReadOnlyMemory<float>(s_vector1),
            ["NullableFloatVector"] = new ReadOnlyMemory<float>(s_vector2)
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
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
            new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
            new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10),
        ]);

        var dataModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",
            ["StringDataProp"] = null,
            ["NullableIntDataProp"] = null,
            ["NullableFloatVector"] = null
        };

        var sut = new AzureAISearchDynamicDataModelMapper(model);

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
        var sut = new AzureAISearchDynamicDataModelMapper(s_model);
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
        Assert.Equal("key", dataModel["Key"]);
        Assert.Equal("string", dataModel["StringDataProp"]);
        Assert.Equal(1, dataModel["IntDataProp"]);
        Assert.Equal(2, dataModel["NullableIntDataProp"]);
        Assert.Equal(3L, dataModel["LongDataProp"]);
        Assert.Equal(4L, dataModel["NullableLongDataProp"]);
        Assert.Equal(5.0f, dataModel["FloatDataProp"]);
        Assert.Equal(6.0f, dataModel["NullableFloatDataProp"]);
        Assert.Equal(7.0, dataModel["DoubleDataProp"]);
        Assert.Equal(8.0, dataModel["NullableDoubleDataProp"]);
        Assert.Equal(true, dataModel["BoolDataProp"]);
        Assert.Equal(false, dataModel["NullableBoolDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), dataModel["DateTimeOffsetDataProp"]);
        Assert.Equal(new DateTimeOffset(2021, 1, 1, 0, 0, 0, TimeSpan.Zero), dataModel["NullableDateTimeOffsetDataProp"]);
        Assert.Equal(s_taglist, dataModel["TagListDataProp"]);
        Assert.Equal(s_vector1, ((ReadOnlyMemory<float>)dataModel["FloatVector"]!).ToArray());
        Assert.Equal(s_vector2, ((ReadOnlyMemory<float>)dataModel["NullableFloatVector"]!)!.ToArray());
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
            new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10),
        ]);

        var storageModel = new JsonObject();
        storageModel["Key"] = "key";
        storageModel["StringDataProp"] = null;
        storageModel["NullableIntDataProp"] = null;
        storageModel["NullableFloatVector"] = null;

        var sut = new AzureAISearchDynamicDataModelMapper(model);

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
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
            new VectorStoreRecordDataProperty("NullableIntDataProp", typeof(int?)),
            new VectorStoreRecordVectorProperty("NullableFloatVector", typeof(ReadOnlyMemory<float>?), 10),
        ]);

        var sut = new AzureAISearchDynamicDataModelMapper(model);
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
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
            new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
        ]);

        var dataModel = new Dictionary<string, object?> { ["Key"] = "key" };
        var sut = new AzureAISearchDynamicDataModelMapper(model);

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
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringDataProp", typeof(string)),
            new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
        ]);

        var storageModel = new JsonObject();
        storageModel["Key"] = "key";

        var sut = new AzureAISearchDynamicDataModelMapper(model);

        // Act
        var dataModel = sut.MapFromStorageToDataModel(storageModel, new StorageToDataModelMapperOptions { IncludeVectors = true });

        // Assert
        Assert.Equal("key", dataModel["Key"]);
        Assert.False(dataModel.ContainsKey("StringDataProp"));
        Assert.False(dataModel.ContainsKey("FloatVector"));
    }

    private static VectorStoreRecordModel BuildModel(List<VectorStoreRecordProperty> properties)
        => new VectorStoreRecordJsonModelBuilder(AzureAISearchModelBuilder.s_modelBuildingOptions)
            .Build(
                typeof(Dictionary<string, object?>),
                new() { Properties = properties },
                defaultEmbeddingGenerator: null);
}
