// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Bson;
using Xunit;

namespace SemanticKernel.Connectors.MongoDB.UnitTests;

/// <summary>
/// Unit tests for <see cref="MongoDBVectorStoreRecordMapper{TRecord}"/> class.
/// </summary>
public sealed class MongoDBVectorStoreRecordMapperTests
{
    private readonly MongoDBVectorStoreRecordMapper<MongoDBHotelModel> _sut;

    public MongoDBVectorStoreRecordMapperTests()
    {
        var keyProperty = new VectorStoreRecordKeyProperty("HotelId", typeof(string));

        var definition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                keyProperty,
                new VectorStoreRecordDataProperty("HotelName", typeof(string)),
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), 10)
            ]
        };

        this._sut = new(new MongoDBModelBuilder().Build(typeof(MongoDBHotelModel), definition, defaultEmbeddingGenerator: null));
    }

    [Fact]
    public void MapFromDataToStorageModelReturnsValidObject()
    {
        // Arrange
        var hotel = new MongoDBHotelModel("key")
        {
            HotelName = "Test Name",
            Tags = ["tag1", "tag2"],
            ParkingIncluded = true,
            DescriptionEmbedding = new ReadOnlyMemory<float>([1f, 2f, 3f])
        };

        // Act
        var document = this._sut.MapFromDataToStorageModel(hotel, generatedEmbeddings: null);

        // Assert
        Assert.NotNull(document);

        Assert.Equal("key", document["_id"]);
        Assert.Equal("Test Name", document["HotelName"]);
        Assert.Equal(["tag1", "tag2"], document["Tags"].AsBsonArray);
        Assert.True(document["parking_is_included"].AsBoolean);
        Assert.Equal([1f, 2f, 3f], document["DescriptionEmbedding"].AsBsonArray);
    }

    [Fact]
    public void MapFromStorageToDataModelReturnsValidObject()
    {
        // Arrange
        var document = new BsonDocument
        {
            ["_id"] = "key",
            ["HotelName"] = "Test Name",
            ["Tags"] = BsonArray.Create(new List<string> { "tag1", "tag2" }),
            ["parking_is_included"] = BsonValue.Create(true),
            ["DescriptionEmbedding"] = BsonArray.Create(new List<float> { 1f, 2f, 3f })
        };

        // Act
        var hotel = this._sut.MapFromStorageToDataModel(document, new());

        // Assert
        Assert.NotNull(hotel);

        Assert.Equal("key", hotel.HotelId);
        Assert.Equal("Test Name", hotel.HotelName);
        Assert.Equal(["tag1", "tag2"], hotel.Tags);
        Assert.True(hotel.ParkingIncluded);
        Assert.True(new ReadOnlyMemory<float>([1f, 2f, 3f]).Span.SequenceEqual(hotel.DescriptionEmbedding!.Value.Span));
    }
}
