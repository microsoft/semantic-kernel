// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using Xunit;

namespace SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisJsonMapper{TConsumerDataModel}"/> class.
/// </summary>
public sealed class RedisJsonMapperTests
{
    [Fact]
    public void MapsAllFieldsFromDataToStorageModel()
    {
        // Arrange.
        var model = new RedisJsonModelBuilder(RedisJsonCollection<string, MultiPropsModel>.ModelBuildingOptions)
            .Build(typeof(MultiPropsModel), definition: null, defaultEmbeddingGenerator: null, JsonSerializerOptions.Default);
        var sut = new RedisJsonMapper<MultiPropsModel>(model, JsonSerializerOptions.Default);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateModel("test key"), recordIndex: 0, generatedEmbeddings: null);

        // Assert.
        Assert.NotNull(actual.Node);
        Assert.Equal("test key", actual.Key);
        var jsonObject = actual.Node.AsObject();
        Assert.Equal("data 1", jsonObject?["Data1"]?.ToString());
        Assert.Equal("data 2", jsonObject?["Data2"]?.ToString());
        Assert.Equal(new float[] { 1, 2, 3, 4 }, jsonObject?["Vector1"]?.AsArray().GetValues<float>().ToArray());
        Assert.Equal(new float[] { 5, 6, 7, 8 }, jsonObject?["Vector2"]?.AsArray().GetValues<float>().ToArray());
    }

    [Fact]
    public void MapsAllFieldsFromDataToStorageModelWithCustomSerializerOptions()
    {
        // Arrange.
        var jsonSerializerOptions = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
        var model = new RedisJsonModelBuilder(RedisJsonCollection<string, MultiPropsModel>.ModelBuildingOptions)
            .Build(typeof(MultiPropsModel), definition: null, defaultEmbeddingGenerator: null, jsonSerializerOptions);
        var sut = new RedisJsonMapper<MultiPropsModel>(model, jsonSerializerOptions);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateModel("test key"), recordIndex: 0, generatedEmbeddings: null);

        // Assert.
        Assert.NotNull(actual.Node);
        Assert.Equal("test key", actual.Key);
        var jsonObject = actual.Node.AsObject();
        Assert.Equal("data 1", jsonObject?["data1"]?.ToString());
        Assert.Equal("data 2", jsonObject?["data2"]?.ToString());
        Assert.Equal(new float[] { 1, 2, 3, 4 }, jsonObject?["vector1"]?.AsArray().GetValues<float>().ToArray());
        Assert.Equal(new float[] { 5, 6, 7, 8 }, jsonObject?["vector2"]?.AsArray().GetValues<float>().ToArray());
    }

    [Fact]
    public void MapsAllFieldsFromStorageToDataModel()
    {
        // Arrange.
        var model = new RedisJsonModelBuilder(RedisJsonCollection<string, MultiPropsModel>.ModelBuildingOptions)
            .Build(typeof(MultiPropsModel), definition: null, defaultEmbeddingGenerator: null, JsonSerializerOptions.Default);
        var sut = new RedisJsonMapper<MultiPropsModel>(model, JsonSerializerOptions.Default);

        // Act.
        var jsonObject = new JsonObject
        {
            { "Data1", "data 1" },
            { "Data2", "data 2" },
            { "Vector1", new JsonArray(new[] { 1, 2, 3, 4 }.Select(x => JsonValue.Create(x)).ToArray()) },
            { "Vector2", new JsonArray(new[] { 5, 6, 7, 8 }.Select(x => JsonValue.Create(x)).ToArray()) }
        };
        var actual = sut.MapFromStorageToDataModel(("test key", jsonObject), includeVectors: true);

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal("test key", actual.Key);
        Assert.Equal("data 1", actual.Data1);
        Assert.Equal("data 2", actual.Data2);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector1!.Value.ToArray());
        Assert.Equal(new float[] { 5, 6, 7, 8 }, actual.Vector2!.Value.ToArray());
    }

    [Fact]
    public void MapsAllFieldsFromStorageToDataModelWithCustomSerializerOptions()
    {
        // Arrange.
        var jsonSerializerOptions = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
        var model = new RedisJsonModelBuilder(RedisJsonCollection<string, MultiPropsModel>.ModelBuildingOptions)
            .Build(typeof(MultiPropsModel), definition: null, defaultEmbeddingGenerator: null, jsonSerializerOptions);
        var sut = new RedisJsonMapper<MultiPropsModel>(model, jsonSerializerOptions);

        // Act.
        var jsonObject = new JsonObject
        {
            { "data1", "data 1" },
            { "data2", "data 2" },
            { "vector1", new JsonArray(new[] { 1, 2, 3, 4 }.Select(x => JsonValue.Create(x)).ToArray()) },
            { "vector2", new JsonArray(new[] { 5, 6, 7, 8 }.Select(x => JsonValue.Create(x)).ToArray()) }
        };
        var actual = sut.MapFromStorageToDataModel(("test key", jsonObject), includeVectors: true);

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal("test key", actual.Key);
        Assert.Equal("data 1", actual.Data1);
        Assert.Equal("data 2", actual.Data2);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector1!.Value.ToArray());
        Assert.Equal(new float[] { 5, 6, 7, 8 }, actual.Vector2!.Value.ToArray());
    }

    private static MultiPropsModel CreateModel(string key)
    {
        return new MultiPropsModel
        {
            Key = key,
            Data1 = "data 1",
            Data2 = "data 2",
            Vector1 = new float[] { 1, 2, 3, 4 },
            Vector2 = new float[] { 5, 6, 7, 8 },
            NotAnnotated = "notAnnotated",
        };
    }

    private sealed class MultiPropsModel
    {
        [VectorStoreKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreData]
        public string Data1 { get; set; } = string.Empty;

        [VectorStoreData]
        public string Data2 { get; set; } = string.Empty;

        [VectorStoreVector(10)]
        public ReadOnlyMemory<float>? Vector1 { get; set; }

        [VectorStoreVector(10)]
        public ReadOnlyMemory<float>? Vector2 { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }
}
