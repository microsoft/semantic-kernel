// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisJsonGenericDataModelMapper"/> class.
/// </summary>
public class RedisJsonGenericDataModelMapperTests
{
    private static readonly float[] s_floatVector = new float[] { 1.0f, 2.0f, 3.0f, 4.0f };

    private static readonly VectorStoreRecordDefinition s_vectorStoreRecordDefinition = new()
    {
        Properties = new List<VectorStoreRecordProperty>()
        {
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringData", typeof(string)) { StoragePropertyName = "storage_string_data" },
            new VectorStoreRecordDataProperty("IntData", typeof(int)),
            new VectorStoreRecordDataProperty("NullableIntData", typeof(int?)),
            new VectorStoreRecordDataProperty("ComplexObjectData", typeof(ComplexObject)),
            new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>)),
        }
    };

    [Fact]
    public void MapFromDataToStorageModelMapsAllSupportedTypes()
    {
        // Arrange.
        var sut = new RedisJsonGenericDataModelMapper(s_vectorStoreRecordDefinition.Properties, JsonSerializerOptions.Default);
        var dataModel = new VectorStoreGenericDataModel<string>("key")
        {
            Data =
            {
                ["StringData"] = "data 1",
                ["IntData"] = 1,
                ["NullableIntData"] = 2,
                ["ComplexObjectData"] = new ComplexObject { Prop1 = "prop 1", Prop2 = "prop 2" },
            },
            Vectors =
            {
                ["FloatVector"] = new ReadOnlyMemory<float>(s_floatVector),
            },
        };

        // Act.
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal("key", storageModel.Key);
        Assert.Equal("data 1", (string)storageModel.Node["storage_string_data"]!);
        Assert.Equal(1, (int)storageModel.Node["IntData"]!);
        Assert.Equal(2, (int?)storageModel.Node["NullableIntData"]!);
        Assert.Equal("prop 1", (string)storageModel.Node["ComplexObjectData"]!.AsObject()["Prop1"]!);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, storageModel.Node["FloatVector"]?.AsArray().GetValues<float>().ToArray());
    }

    [Fact]
    public void MapFromDataToStorageModelMapsNullValues()
    {
        // Arrange.
        var sut = new RedisJsonGenericDataModelMapper(s_vectorStoreRecordDefinition.Properties, JsonSerializerOptions.Default);
        var dataModel = new VectorStoreGenericDataModel<string>("key")
        {
            Data =
            {
                ["StringData"] = null,
                ["IntData"] = null,
                ["NullableIntData"] = null,
                ["ComplexObjectData"] = null,
            },
            Vectors =
            {
                ["FloatVector"] = null,
            },
        };

        // Act.
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

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
        var sut = new RedisJsonGenericDataModelMapper(s_vectorStoreRecordDefinition.Properties, JsonSerializerOptions.Default);
        var storageModel = new JsonObject();
        storageModel.Add("storage_string_data", "data 1");
        storageModel.Add("IntData", 1);
        storageModel.Add("NullableIntData", 2);
        storageModel.Add("ComplexObjectData", new JsonObject(new KeyValuePair<string, JsonNode?>[] { new("Prop1", JsonValue.Create("prop 1")), new("Prop2", JsonValue.Create("prop 2")) }));
        storageModel.Add("FloatVector", new JsonArray(new[] { 1, 2, 3, 4 }.Select(x => JsonValue.Create(x)).ToArray()));

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", storageModel), new() { IncludeVectors = true });

        // Assert.
        Assert.Equal("key", dataModel.Key);
        Assert.Equal("data 1", dataModel.Data["StringData"]);
        Assert.Equal(1, dataModel.Data["IntData"]);
        Assert.Equal(2, dataModel.Data["NullableIntData"]);
        Assert.Equal("prop 1", ((ComplexObject)dataModel.Data["ComplexObjectData"]!).Prop1);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, ((ReadOnlyMemory<float>)dataModel.Vectors["FloatVector"]!).ToArray());
    }

    [Fact]
    public void MapFromStorageToDataModelMapsNullValues()
    {
        // Arrange.
        var sut = new RedisJsonGenericDataModelMapper(s_vectorStoreRecordDefinition.Properties, JsonSerializerOptions.Default);
        var storageModel = new JsonObject();
        storageModel.Add("storage_string_data", null);
        storageModel.Add("IntData", null);
        storageModel.Add("NullableIntData", null);
        storageModel.Add("ComplexObjectData", null);
        storageModel.Add("FloatVector", null);

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", storageModel), new() { IncludeVectors = true });

        // Assert.
        Assert.Equal("key", dataModel.Key);
        Assert.Null(dataModel.Data["StringData"]);
        Assert.Null(dataModel.Data["IntData"]);
        Assert.Null(dataModel.Data["NullableIntData"]);
        Assert.Null(dataModel.Data["ComplexObjectData"]);
        Assert.Null(dataModel.Vectors["FloatVector"]);
    }

    [Fact]
    public void MapFromDataToStorageModelSkipsMissingProperties()
    {
        // Arrange.
        var sut = new RedisJsonGenericDataModelMapper(s_vectorStoreRecordDefinition.Properties, JsonSerializerOptions.Default);
        var dataModel = new VectorStoreGenericDataModel<string>("key")
        {
            Data = { },
            Vectors = { },
        };

        // Act.
        var storageModel = sut.MapFromDataToStorageModel(dataModel);

        // Assert
        Assert.Equal("key", storageModel.Key);
        Assert.Empty(storageModel.Node.AsObject());
    }

    [Fact]
    public void MapFromStorageToDataModelSkipsMissingProperties()
    {
        // Arrange.
        var storageModel = new JsonObject();

        var sut = new RedisJsonGenericDataModelMapper(s_vectorStoreRecordDefinition.Properties, JsonSerializerOptions.Default);

        // Act.
        var dataModel = sut.MapFromStorageToDataModel(("key", storageModel), new() { IncludeVectors = true });

        // Assert.
        Assert.Equal("key", dataModel.Key);
        Assert.Empty(dataModel.Data);
        Assert.Empty(dataModel.Vectors);
    }

    private sealed class ComplexObject
    {
        public string Prop1 { get; set; } = string.Empty;

        public string Prop2 { get; set; } = string.Empty;
    }
}
