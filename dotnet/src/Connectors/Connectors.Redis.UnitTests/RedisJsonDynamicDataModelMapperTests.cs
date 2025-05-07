// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisJsonDynamicDataModelMapper"/> class.
/// </summary>
public class RedisJsonDynamicDataModelMapperTests
{
    private static readonly float[] s_floatVector = new float[] { 1.0f, 2.0f, 3.0f, 4.0f };

    private static readonly VectorStoreRecordModel s_model
        = new VectorStoreRecordJsonModelBuilder(RedisJsonVectorStoreRecordCollection<object, Dictionary<string, object?>>.ModelBuildingOptions)
            .Build(
                typeof(Dictionary<string, object?>),
                new()
                {
                    Properties =
                    [
                        new VectorStoreRecordKeyProperty("Key", typeof(string)),
                        new VectorStoreRecordDataProperty("StringData", typeof(string)),
                        new VectorStoreRecordDataProperty("IntData", typeof(int)),
                        new VectorStoreRecordDataProperty("NullableIntData", typeof(int?)),
                        new VectorStoreRecordDataProperty("ComplexObjectData", typeof(ComplexObject)),
                        new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
                    ]
                },
                defaultEmbeddingGenerator: null);

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange.
        var sut = new RedisJsonDynamicDataModelMapper(s_model, JsonSerializerOptions.Default);
        var dataModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",
            ["StringData"] = "data 1",
            ["IntData"] = 1,
            ["NullableIntData"] = 2,
            ["ComplexObjectData"] = new ComplexObject { Prop1 = "prop 1", Prop2 = "prop 2" },
            ["FloatVector"] = new ReadOnlyMemory<float>(s_floatVector)
        };

        // Act.
        var storageModel = sut.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal("key", storageModel.Key);
        Assert.Equal("data 1", (string)storageModel.Node["StringData"]!);
        Assert.Equal(1, (int)storageModel.Node["IntData"]!);
        Assert.Equal(2, (int?)storageModel.Node["NullableIntData"]!);
        Assert.Equal("prop 1", (string)storageModel.Node["ComplexObjectData"]!.AsObject()["Prop1"]!);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, storageModel.Node["FloatVector"]?.AsArray().GetValues<float>().ToArray());
    }

    [Fact]
    public void MapFromDataToStorageModelMapsNullValues()
    {
        // Arrange.
        var sut = new RedisJsonDynamicDataModelMapper(s_model, JsonSerializerOptions.Default);
        var dataModel = new Dictionary<string, object?>
        {
            ["Key"] = "key",
            ["StringData"] = null,
            ["IntData"] = null,
            ["NullableIntData"] = null,
            ["ComplexObjectData"] = null,
            ["FloatVector"] = null,
        };

        // Act.
        var storageModel = sut.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal("key", storageModel.Key);
        Assert.Null(storageModel.Node["storage_string_data"]);
        Assert.Null(storageModel.Node["IntData"]);
        Assert.Null(storageModel.Node["NullableIntData"]);
        Assert.Null(storageModel.Node["ComplexObjectData"]);
        Assert.Null(storageModel.Node["FloatVector"]);
    }

    [Fact]
    public void MapFromStorageToDataModelMapsAllSupportedTypes()
    {
        // Arrange.
        var sut = new RedisJsonDynamicDataModelMapper(s_model, JsonSerializerOptions.Default);
        var storageModel = new JsonObject
        {
            { "StringData", "data 1" },
            { "IntData", 1 },
            { "NullableIntData", 2 },
            { "ComplexObjectData", new JsonObject(new KeyValuePair<string, JsonNode?>[] { new("Prop1", JsonValue.Create("prop 1")), new("Prop2", JsonValue.Create("prop 2")) }) },
            { "FloatVector", new JsonArray(new[] { 1, 2, 3, 4 }.Select(x => JsonValue.Create(x)).ToArray()) }
        };

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", storageModel), new() { IncludeVectors = true });

        // Assert.
        Assert.Equal("key", dataModel["Key"]);
        Assert.Equal("data 1", dataModel["StringData"]);
        Assert.Equal(1, dataModel["IntData"]);
        Assert.Equal(2, dataModel["NullableIntData"]);
        Assert.Equal("prop 1", ((ComplexObject)dataModel["ComplexObjectData"]!).Prop1);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, ((ReadOnlyMemory<float>)dataModel["FloatVector"]!).ToArray());
    }

    [Fact]
    public void MapFromStorageToDataModelMapsNullValues()
    {
        // Arrange.
        var sut = new RedisJsonDynamicDataModelMapper(s_model, JsonSerializerOptions.Default);
        var storageModel = new JsonObject
        {
            { "StringData", null },
            { "IntData", null },
            { "NullableIntData", null },
            { "ComplexObjectData", null },
            { "FloatVector", null }
        };

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", storageModel), new() { IncludeVectors = true });

        // Assert.
        Assert.Equal("key", dataModel["Key"]);
        Assert.Null(dataModel["StringData"]);
        Assert.Null(dataModel["IntData"]);
        Assert.Null(dataModel["NullableIntData"]);
        Assert.Null(dataModel["ComplexObjectData"]);
        Assert.Null(dataModel["FloatVector"]);
    }

    [Fact]
    public void MapFromDataToStorageModelSkipsMissingProperties()
    {
        // Arrange.
        var sut = new RedisJsonDynamicDataModelMapper(s_model, JsonSerializerOptions.Default);
        var dataModel = new Dictionary<string, object?> { ["Key"] = "key" };

        // Act.
        var storageModel = sut.MapFromDataToStorageModel(dataModel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.Equal("key", storageModel.Key);
        Assert.Empty(storageModel.Node.AsObject());
    }

    [Fact]
    public void MapFromStorageToDataModelSkipsMissingProperties()
    {
        // Arrange.
        var storageModel = new JsonObject();

        var sut = new RedisJsonDynamicDataModelMapper(s_model, JsonSerializerOptions.Default);

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", storageModel), new() { IncludeVectors = true });

        // Assert.
        Assert.Equal("key", dataModel["Key"]);
        Assert.Single(dataModel);
    }

    private sealed class ComplexObject
    {
        public string Prop1 { get; set; } = string.Empty;

        public string Prop2 { get; set; } = string.Empty;
    }
}
