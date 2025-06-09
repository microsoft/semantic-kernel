// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

/// <summary>
/// Unit tests for <see cref="WeaviateMapper{TRecord}"/> class.
/// </summary>
public sealed class WeaviateMapperTests
{
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Converters =
        {
            new WeaviateDateTimeOffsetConverter(),
            new WeaviateNullableDateTimeOffsetConverter()
        }
    };

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapFromDataToStorageModelReturnsValidObject(bool hasNamedVectors)
    {
        var key = new Guid("55555555-5555-5555-5555-555555555555");
        // Arrange
        var hotel = new WeaviateHotel
        {
            HotelId = key,
            HotelName = "Test Name",
            Tags = ["tag1", "tag2"],
            DescriptionEmbedding = new ReadOnlyMemory<float>([1f, 2f, 3f])
        };

        var sut = GetMapper(hasNamedVectors);

        // Act
        var document = sut.MapFromDataToStorageModel(hotel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.NotNull(document);

        Assert.Equal(key, document["id"]!.GetValue<Guid>());
        Assert.Equal("Test Name", document["properties"]!["hotelName"]!.GetValue<string>());
        Assert.Equal(["tag1", "tag2"], document["properties"]!["tags"]!.AsArray().Select(l => l!.GetValue<string>()));

        var vectorNode = hasNamedVectors ? document["vectors"]!["descriptionEmbedding"] : document["vector"];

        Assert.Equal([1f, 2f, 3f], vectorNode!.AsArray().Select(l => l!.GetValue<float>()));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapFromStorageToDataModelReturnsValidObject(bool hasNamedVectors)
    {
        var key = new Guid("55555555-5555-5555-5555-555555555555");

        // Arrange
        var document = new JsonObject
        {
            ["id"] = key,
            ["properties"] = new JsonObject(),
            ["vectors"] = new JsonObject()
        };

        document["properties"]!["hotelName"] = "Test Name";
        document["properties"]!["tags"] = new JsonArray(new List<string> { "tag1", "tag2" }.Select(l => JsonValue.Create(l)).ToArray());

        var vectorNode = new JsonArray(new List<float> { 1f, 2f, 3f }.Select(l => JsonValue.Create(l)).ToArray());

        if (hasNamedVectors)
        {
            document["vectors"]!["descriptionEmbedding"] = vectorNode;
        }
        else
        {
            document["vector"] = vectorNode;
        }

        var sut = GetMapper(hasNamedVectors);

        // Act
        var hotel = sut.MapFromStorageToDataModel(document, includeVectors: true);

        // Assert
        Assert.NotNull(hotel);

        Assert.Equal(key, hotel.HotelId);
        Assert.Equal("Test Name", hotel.HotelName);
        Assert.Equal(["tag1", "tag2"], hotel.Tags);
        Assert.True(new ReadOnlyMemory<float>([1f, 2f, 3f]).Span.SequenceEqual(hotel.DescriptionEmbedding!.Value.Span));
    }

    #region private

    private static WeaviateMapper<WeaviateHotel> GetMapper(bool hasNamedVectors) => new(
            "CollectionName",
            hasNamedVectors,
            new WeaviateModelBuilder(hasNamedVectors)
                .Build(
                    typeof(WeaviateHotel),
                    new VectorStoreCollectionDefinition
                    {
                        Properties =
                        [
                            new VectorStoreKeyProperty("HotelId", typeof(Guid)),
                            new VectorStoreDataProperty("HotelName", typeof(string)),
                            new VectorStoreDataProperty("Tags", typeof(List<string>)),
                            new VectorStoreVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>), 10)
                        ]
                    },
                    defaultEmbeddingGenerator: null,
                    s_jsonSerializerOptions),
            s_jsonSerializerOptions);

    #endregion
}
