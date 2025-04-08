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
/// Unit tests for <see cref="WeaviateVectorStoreRecordMapper{TRecord}"/> class.
/// </summary>
public sealed class WeaviateVectorStoreRecordMapperTests
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
    public void MapFromDataToStorageModelReturnsValidObject(bool useSingleVector)
    {
        // Arrange
        var hotel = new WeaviateHotel
        {
            HotelId = new Guid("55555555-5555-5555-5555-555555555555"),
            HotelName = "Test Name",
            Tags = ["tag1", "tag2"],
            DescriptionEmbedding = new ReadOnlyMemory<float>([1f, 2f, 3f])
        };

        var sut = GetMapper(useSingleVector);

        // Act
        var document = sut.MapFromDataToStorageModel(hotel);

        // Assert
        Assert.NotNull(document);

        Assert.Equal("55555555-5555-5555-5555-555555555555", document["id"]!.GetValue<string>());
        Assert.Equal("Test Name", document["properties"]!["hotelName"]!.GetValue<string>());
        Assert.Equal(["tag1", "tag2"], document["properties"]!["tags"]!.AsArray().Select(l => l!.GetValue<string>()));

        var vectorNode = useSingleVector ? document["vector"] : document["vectors"]!["descriptionEmbedding"];

        Assert.Equal([1f, 2f, 3f], vectorNode!.AsArray().Select(l => l!.GetValue<float>()));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapFromStorageToDataModelReturnsValidObject(bool useSingleVector)
    {
        // Arrange
        var document = new JsonObject
        {
            ["id"] = "55555555-5555-5555-5555-555555555555",
            ["properties"] = new JsonObject(),
            ["vectors"] = new JsonObject()
        };

        document["properties"]!["hotelName"] = "Test Name";
        document["properties"]!["tags"] = new JsonArray(new List<string> { "tag1", "tag2" }.Select(l => JsonValue.Create(l)).ToArray());

        var vectorNode = new JsonArray(new List<float> { 1f, 2f, 3f }.Select(l => JsonValue.Create(l)).ToArray());

        if (useSingleVector)
        {
            document["vector"] = vectorNode;
        }
        else
        {
            document["vectors"]!["descriptionEmbedding"] = vectorNode;
        }

        var sut = GetMapper(useSingleVector);

        // Act
        var hotel = sut.MapFromStorageToDataModel(document, new() { IncludeVectors = true });

        // Assert
        Assert.NotNull(hotel);

        Assert.Equal(new Guid("55555555-5555-5555-5555-555555555555"), hotel.HotelId);
        Assert.Equal("Test Name", hotel.HotelName);
        Assert.Equal(["tag1", "tag2"], hotel.Tags);
        Assert.True(new ReadOnlyMemory<float>([1f, 2f, 3f]).Span.SequenceEqual(hotel.DescriptionEmbedding!.Value.Span));
    }

    #region private

    private static WeaviateVectorStoreRecordMapper<WeaviateHotel> GetMapper(bool useSingleVector) => new(
        "CollectionName",
        useSingleVector,
        new WeaviateModelBuilder(useSingleVector)
        .Build(
            typeof(VectorStoreGenericDataModel<Guid>),
            new VectorStoreRecordDefinition
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty("HotelId", typeof(Guid)),
                    new VectorStoreRecordDataProperty("HotelName", typeof(string)),
                    new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                    new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>))
                ]
            },
            s_jsonSerializerOptions),
        s_jsonSerializerOptions);

    #endregion
}
