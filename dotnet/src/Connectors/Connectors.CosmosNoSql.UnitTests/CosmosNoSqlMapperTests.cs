// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using Xunit;

namespace SemanticKernel.Connectors.CosmosNoSql.UnitTests;

/// <summary>
/// Unit tests for <see cref="CosmosNoSqlMapper{TRecord}"/> class.
/// </summary>
public sealed class CosmosNoSqlMapperTests
{
    private readonly CosmosNoSqlMapper<CosmosNoSqlHotel> _sut
        = new(
            new CosmosNoSqlModelBuilder().BuildDynamic(
                new()
                {
                    Properties =
                    [
                        new VectorStoreKeyProperty("HotelId", typeof(string)),
                        new VectorStoreVectorProperty("TestProperty1", typeof(ReadOnlyMemory<float>), 10) { StorageName = "test_property_1" },
                        new VectorStoreDataProperty("TestProperty2", typeof(string)) { StorageName = "test_property_2" },
                        new VectorStoreDataProperty("TestProperty3", typeof(string)) { StorageName = "test_property_3" }
                    ]
                },
                defaultEmbeddingGenerator: null,
                JsonSerializerOptions.Default),
            JsonSerializerOptions.Default);

    [Fact]
    public void MapFromDataToStorageModelReturnsValidObject()
    {
        // Arrange
        var hotel = new CosmosNoSqlHotel("key")
        {
            HotelName = "Test Name",
            Tags = ["tag1", "tag2"],
            DescriptionEmbedding = new ReadOnlyMemory<float>([1f, 2f, 3f])
        };

        // Act
        var document = this._sut.MapFromDataToStorageModel(hotel, recordIndex: 0, generatedEmbeddings: null);

        // Assert
        Assert.NotNull(document);

        Assert.Equal("key", document["id"]!.GetValue<string>());
        Assert.Equal("Test Name", document["HotelName"]!.GetValue<string>());
        Assert.Equal(["tag1", "tag2"], document["Tags"]!.AsArray().Select(l => l!.GetValue<string>()));
        Assert.Equal([1f, 2f, 3f], document["description_embedding"]!.AsArray().Select(l => l!.GetValue<float>()));
    }

    [Fact]
    public void MapFromStorageToDataModelReturnsValidObject()
    {
        // Arrange
        var document = new JsonObject
        {
            ["id"] = "key",
            ["HotelName"] = "Test Name",
            ["Tags"] = new JsonArray(new List<string> { "tag1", "tag2" }.Select(l => JsonValue.Create(l)).ToArray()),
            ["description_embedding"] = new JsonArray(new List<float> { 1f, 2f, 3f }.Select(l => JsonValue.Create(l)).ToArray()),
        };

        // Act
        var hotel = this._sut.MapFromStorageToDataModel(document, new());

        // Assert
        Assert.NotNull(hotel);

        Assert.Equal("key", hotel.HotelId);
        Assert.Equal("Test Name", hotel.HotelName);
        Assert.Equal(["tag1", "tag2"], hotel.Tags);
        Assert.True(new ReadOnlyMemory<float>([1f, 2f, 3f]).Span.SequenceEqual(hotel.DescriptionEmbedding!.Value.Span));
    }
}
