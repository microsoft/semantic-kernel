// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Microsoft.SemanticKernel.Data;
using MongoDB.Bson;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBMongoDB.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBMongoDBVectorStoreRecordMapper{TRecord}"/> class.
/// </summary>
public sealed class AzureCosmosDBMongoDBVectorStoreRecordMapperTests
{
    private readonly AzureCosmosDBMongoDBVectorStoreRecordMapper<AzureCosmosDBMongoDBHotelModel> _sut;

    public AzureCosmosDBMongoDBVectorStoreRecordMapperTests()
    {
<<<<<<< HEAD
        var keyProperty = new VectorStoreRecordKeyProperty("HotelId", typeof(string));

=======
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
        var definition = new VectorStoreRecordDefinition
        {
            Properties =
            [
<<<<<<< HEAD
                keyProperty,
                new VectorStoreRecordDataProperty("HotelName", typeof(string)),
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?))
            ]
        };

        this._sut = new(definition, keyProperty.DataModelPropertyName);
=======
                new VectorStoreRecordKeyProperty("HotelId", typeof(string)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)),
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { StoragePropertyName = "description_embedding " }
            ]
        };

        var storagePropertyNames = new Dictionary<string, string>
        {
            ["HotelId"] = "HotelId",
            ["HotelName"] = "HotelName",
            ["Tags"] = "Tags",
            ["DescriptionEmbedding"] = "description_embedding",
        };

        this._sut = new(definition, storagePropertyNames);
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
    }

    [Fact]
    public void MapFromDataToStorageModelReturnsValidObject()
    {
        // Arrange
        var hotel = new AzureCosmosDBMongoDBHotelModel("key")
        {
            HotelName = "Test Name",
            Tags = ["tag1", "tag2"],
<<<<<<< HEAD
            ParkingIncluded = true,
=======
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
            DescriptionEmbedding = new ReadOnlyMemory<float>([1f, 2f, 3f])
        };

        // Act
        var document = this._sut.MapFromDataToStorageModel(hotel);

        // Assert
        Assert.NotNull(document);

        Assert.Equal("key", document["_id"]);
        Assert.Equal("Test Name", document["HotelName"]);
        Assert.Equal(["tag1", "tag2"], document["Tags"].AsBsonArray);
<<<<<<< HEAD
        Assert.True(document["parking_is_included"].AsBoolean);
        Assert.Equal([1f, 2f, 3f], document["DescriptionEmbedding"].AsBsonArray);
=======
        Assert.Equal([1f, 2f, 3f], document["description_embedding"].AsBsonArray);
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
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
<<<<<<< HEAD
            ["parking_is_included"] = BsonValue.Create(true),
            ["DescriptionEmbedding"] = BsonArray.Create(new List<float> { 1f, 2f, 3f })
=======
            ["description_embedding"] = BsonArray.Create(new List<float> { 1f, 2f, 3f })
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
        };

        // Act
        var hotel = this._sut.MapFromStorageToDataModel(document, new());

        // Assert
        Assert.NotNull(hotel);

        Assert.Equal("key", hotel.HotelId);
        Assert.Equal("Test Name", hotel.HotelName);
        Assert.Equal(["tag1", "tag2"], hotel.Tags);
<<<<<<< HEAD
        Assert.True(hotel.ParkingIncluded);
=======
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
        Assert.True(new ReadOnlyMemory<float>([1f, 2f, 3f]).Span.SequenceEqual(hotel.DescriptionEmbedding!.Value.Span));
    }
}
