// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
<<<<<<< main
using Microsoft.SemanticKernel.Data;
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
using Microsoft.Extensions.VectorData;
>>>>>>> upstream/main
=======
>>>>>>> Stashed changes
using MongoDB.Bson.Serialization.Attributes;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using MongoDB.Bson.Serialization.Attributes;
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
using MongoDB.Bson.Serialization.Attributes;
=======
>>>>>>> Stashed changes
=======
using MongoDB.Bson.Serialization.Attributes;
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
using MongoDB.Bson.Serialization.Attributes;
=======
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

namespace SemanticKernel.Connectors.AzureCosmosDBMongoDB.UnitTests;

public class AzureCosmosDBMongoDBHotelModel(string hotelId)
{
    /// <summary>The key of the record.</summary>
    [VectorStoreRecordKey]
    public string HotelId { get; init; } = hotelId;

    /// <summary>A string metadata field.</summary>
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    [VectorStoreRecordData]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    [VectorStoreRecordData]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    [VectorStoreRecordData]
=======
>>>>>>> Stashed changes
=======
    [VectorStoreRecordData]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    [VectorStoreRecordData(IsFilterable = true)]
=======
    [VectorStoreRecordData]
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
    [VectorStoreRecordData(IsFilterable = true)]
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
    public string? HotelName { get; set; }

    /// <summary>An int metadata field.</summary>
    [VectorStoreRecordData]
    public int HotelCode { get; set; }

    /// <summary>A float metadata field.</summary>
    [VectorStoreRecordData]
    public float? HotelRating { get; set; }

    /// <summary>A bool metadata field.</summary>
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    [BsonElement("parking_is_included")]
    [VectorStoreRecordData]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    [BsonElement("parking_is_included")]
    [VectorStoreRecordData]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    [BsonElement("parking_is_included")]
    [VectorStoreRecordData]
=======
>>>>>>> Stashed changes
=======
    [BsonElement("parking_is_included")]
    [VectorStoreRecordData]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    [BsonElement("parking_is_included")]
    [VectorStoreRecordData]
=======
    [VectorStoreRecordData(StoragePropertyName = "parking_is_included")]
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    public bool ParkingIncluded { get; set; }

    /// <summary>An array metadata field.</summary>
    [VectorStoreRecordData]
    public List<string> Tags { get; set; } = [];

    /// <summary>A data field.</summary>
    [VectorStoreRecordData]
    public string? Description { get; set; }

    /// <summary>A vector field.</summary>
    [VectorStoreRecordVector(Dimensions: 4, DistanceFunction: DistanceFunction.CosineDistance, IndexKind: IndexKind.IvfFlat)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
