// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using MongoDB.Bson.Serialization.Attributes;

namespace SemanticKernel.Connectors.AzureCosmosDBMongoDB.UnitTests;

public class AzureCosmosDBMongoDBHotelModel(string hotelId)
{
    /// <summary>The key of the record.</summary>
    [VectorStoreKeyProperty]
    public string HotelId { get; init; } = hotelId;

    /// <summary>A string metadata field.</summary>
    [VectorStoreDataProperty(IsIndexed = true)]
    public string? HotelName { get; set; }

    /// <summary>An int metadata field.</summary>
    [VectorStoreDataProperty]
    public int HotelCode { get; set; }

    /// <summary>A float metadata field.</summary>
    [VectorStoreDataProperty]
    public float? HotelRating { get; set; }

    /// <summary>A bool metadata field.</summary>
    [BsonElement("parking_is_included")]
    [VectorStoreDataProperty]
    public bool ParkingIncluded { get; set; }

    /// <summary>An array metadata field.</summary>
    [VectorStoreDataProperty]
    public List<string> Tags { get; set; } = [];

    /// <summary>A data field.</summary>
    [VectorStoreDataProperty]
    public string? Description { get; set; }

    /// <summary>A vector field.</summary>
    [VectorStoreVectorProperty(Dimensions: 4, DistanceFunction = DistanceFunction.CosineDistance, IndexKind = IndexKind.IvfFlat)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
