// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisJsonDynamicMapper"/> class.
/// </summary>
public class RedisJsonDynamicMapperTests
{
    private static readonly float[] s_floatVector = new float[] { 1.0f, 2.0f, 3.0f, 4.0f };

    private static readonly CollectionModel s_model
        = new RedisJsonModelBuilder(RedisJsonCollection<object, Dictionary<string, object?>>.ModelBuildingOptions)
            .BuildDynamic(
                new()
                {
                    Properties =
                    [
                        new VectorStoreKeyProperty("Key", typeof(string)),
                        new VectorStoreDataProperty("StringData", typeof(string)),
                        new VectorStoreDataProperty("IntData", typeof(int)),
                        new VectorStoreDataProperty("NullableIntData", typeof(int?)),
                        new VectorStoreDataProperty("ComplexObjectData", typeof(ComplexObject)),
                        new VectorStoreVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
                    ]
                },
                defaultEmbeddingGenerator: null);

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange.
        var sut = new RedisJsonDynamicMapper(s_model, JsonSerializerOptions.Default);
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
        var sut = new RedisJsonDynamicMapper(s_model, JsonSerializerOptions.Default);
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
        var sut = new RedisJsonDynamicMapper(s_model, JsonSerializerOptions.Default);
        var storageModel = new JsonObject
        {
            { "StringData", "data 1" },
            { "IntData", 1 },
            { "NullableIntData", 2 },
            { "ComplexObjectData", new JsonObject(new KeyValuePair<string, JsonNode?>[] { new("Prop1", JsonValue.Create("prop 1")), new("Prop2", JsonValue.Create("prop 2")) }) },
            { "FloatVector", new JsonArray(new float[] { 1, 2, 3, 4 }.Select(x => JsonValue.Create(x)).ToArray()) }
        };

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", storageModel), includeVectors: true);

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
        var sut = new RedisJsonDynamicMapper(s_model, JsonSerializerOptions.Default);
        var storageModel = new JsonObject
        {
            { "StringData", null },
            { "IntData", null },
            { "NullableIntData", null },
            { "ComplexObjectData", null },
            { "FloatVector", null }
        };

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", storageModel), includeVectors: true);

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
        var sut = new RedisJsonDynamicMapper(s_model, JsonSerializerOptions.Default);
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

        var sut = new RedisJsonDynamicMapper(s_model, JsonSerializerOptions.Default);

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", storageModel), includeVectors: true);

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
