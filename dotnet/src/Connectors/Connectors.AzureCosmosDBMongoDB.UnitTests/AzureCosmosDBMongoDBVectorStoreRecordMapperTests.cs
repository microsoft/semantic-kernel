<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

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
        var keyProperty = new VectorStoreRecordKeyProperty("HotelId", typeof(string));

        var definition = new VectorStoreRecordDefinition
        {
            Properties =
            [
                keyProperty,
                new VectorStoreRecordDataProperty("HotelName", typeof(string)),
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?))
            ]
        };

        this._sut = new(definition, keyProperty.DataModelPropertyName);
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
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
        this._sut = new(new VectorStoreRecordPropertyReader(typeof(AzureCosmosDBMongoDBHotelModel), definition, null));
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    }

    [Fact]
    public void MapFromDataToStorageModelReturnsValidObject()
    {
        // Arrange
        var hotel = new AzureCosmosDBMongoDBHotelModel("key")
        {
            HotelName = "Test Name",
            Tags = ["tag1", "tag2"],
            ParkingIncluded = true,
            DescriptionEmbedding = new ReadOnlyMemory<float>([1f, 2f, 3f])
        };

        // Act
        var document = this._sut.MapFromDataToStorageModel(hotel);

        // Assert
        Assert.NotNull(document);

        Assert.Equal("key", document["_id"]);
        Assert.Equal("Test Name", document["HotelName"]);
        Assert.Equal(["tag1", "tag2"], document["Tags"].AsBsonArray);
        Assert.True(document["parking_is_included"].AsBoolean);
        Assert.Equal([1f, 2f, 3f], document["DescriptionEmbedding"].AsBsonArray);
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        Assert.Equal([1f, 2f, 3f], document["description_embedding"].AsBsonArray);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        Assert.Equal([1f, 2f, 3f], document["description_embedding"].AsBsonArray);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
        Assert.Equal([1f, 2f, 3f], document["description_embedding"].AsBsonArray);
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
            ["description_embedding"] = BsonArray.Create(new List<float> { 1f, 2f, 3f })
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            ["description_embedding"] = BsonArray.Create(new List<float> { 1f, 2f, 3f })
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
            ["description_embedding"] = BsonArray.Create(new List<float> { 1f, 2f, 3f })
>>>>>>> main
>>>>>>> Stashed changes
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
