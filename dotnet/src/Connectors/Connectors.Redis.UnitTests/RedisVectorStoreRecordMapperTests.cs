// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisVectorStoreRecordMapper{TConsumerDataModel}"/> class.
/// </summary>
public sealed class RedisVectorStoreRecordMapperTests
{
    [Fact]
    public void MapsAllFieldsFromDataToStorageModel()
    {
        // Arrange.
        var sut = new RedisVectorStoreRecordMapper<MultiPropsModel>("Key");

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateModel("test key"));

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
    public void MapsAllFieldsFromStorageToDataModel()
    {
        // Arrange.
        var sut = new RedisVectorStoreRecordMapper<MultiPropsModel>("Key");

        // Act.
        var actual = sut.MapFromStorageToDataModel(("test key", CreateJsonNode()), new());

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

    private static JsonObject CreateJsonNode()
    {
        var jsonObject = new JsonObject();
        jsonObject.Add("Data1", "data 1");
        jsonObject.Add("Data2", "data 2");
        jsonObject.Add("Vector1", new JsonArray(new[] { 1, 2, 3, 4 }.Select(x => JsonValue.Create(x)).ToArray()));
        jsonObject.Add("Vector2", new JsonArray(new[] { 5, 6, 7, 8 }.Select(x => JsonValue.Create(x)).ToArray()));
        return jsonObject;
    }

    private sealed class MultiPropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData(HasEmbedding = true, EmbeddingPropertyName = "Vector1")]
        public string Data1 { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public string Data2 { get; set; } = string.Empty;

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float>? Vector1 { get; set; }

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float>? Vector2 { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }
}
