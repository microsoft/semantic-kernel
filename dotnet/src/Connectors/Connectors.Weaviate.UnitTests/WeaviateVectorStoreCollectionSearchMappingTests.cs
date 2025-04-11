// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

/// <summary>
/// Unit tests for <see cref="WeaviateVectorStoreCollectionSearchMapping"/> class.
/// </summary>
public sealed class WeaviateVectorStoreCollectionSearchMappingTests
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapSearchResultByDefaultReturnsValidResult(bool hasNamedVectors)
    {
        // Arrange
        var jsonObject = new JsonObject
        {
            ["_additional"] = new JsonObject
            {
                ["distance"] = 0.5,
                ["id"] = "55555555-5555-5555-5555-555555555555"
            },
            ["description"] = "This is a great hotel.",
            ["hotelCode"] = 42,
            ["hotelName"] = "My Hotel",
            ["hotelRating"] = 4.5,
            ["parking_is_included"] = true,
            ["tags"] = new JsonArray(new List<string> { "t1", "t2" }.Select(l => (JsonNode)l).ToArray()),
            ["timestamp"] = "2024-08-28T10:11:12-07:00"
        };

        var vector = new JsonArray(new List<float> { 30, 31, 32, 33 }.Select(l => (JsonNode)l).ToArray());

        if (hasNamedVectors)
        {
            jsonObject["_additional"]!["vectors"] = new JsonObject
            {
                ["descriptionEmbedding"] = vector
            };
        }
        else
        {
            jsonObject["_additional"]!["vector"] = vector;
        }

        // Act
        var (storageModel, score) = WeaviateVectorStoreCollectionSearchMapping.MapSearchResult(jsonObject, "distance", hasNamedVectors);

        // Assert
        Assert.Equal(0.5, score);

        Assert.Equal("55555555-5555-5555-5555-555555555555", storageModel["id"]!.GetValue<string>());
        Assert.Equal("This is a great hotel.", storageModel["properties"]!["description"]!.GetValue<string>());
        Assert.Equal(42, storageModel["properties"]!["hotelCode"]!.GetValue<int>());
        Assert.Equal(4.5, storageModel["properties"]!["hotelRating"]!.GetValue<double>());
        Assert.Equal("My Hotel", storageModel["properties"]!["hotelName"]!.GetValue<string>());
        Assert.True(storageModel["properties"]!["parking_is_included"]!.GetValue<bool>());
        Assert.Equal(["t1", "t2"], storageModel["properties"]!["tags"]!.AsArray().Select(l => l!.GetValue<string>()));
        Assert.Equal("2024-08-28T10:11:12-07:00", storageModel["properties"]!["timestamp"]!.GetValue<string>());

        var vectorProperty = hasNamedVectors ? storageModel["vectors"]!["descriptionEmbedding"] : storageModel["vector"];

        Assert.Equal([30f, 31f, 32f, 33f], vectorProperty!.AsArray().Select(l => l!.GetValue<float>()));
    }
}
