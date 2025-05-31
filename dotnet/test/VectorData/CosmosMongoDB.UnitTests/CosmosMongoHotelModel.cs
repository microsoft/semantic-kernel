// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using MongoDB.Bson.Serialization.Attributes;

namespace SemanticKernel.Connectors.CosmosMongoDB.UnitTests;

public class CosmosMongoHotelModel(string hotelId)
{
    /// <summary>The key of the record.</summary>
    [VectorStoreKey]
    public string HotelId { get; init; } = hotelId;

    /// <summary>A string metadata field.</summary>
    [VectorStoreData(IsIndexed = true)]
    public string? HotelName { get; set; }

    /// <summary>An int metadata field.</summary>
    [VectorStoreData]
    public int HotelCode { get; set; }

    /// <summary>A float metadata field.</summary>
    [VectorStoreData]
    public float? HotelRating { get; set; }

    /// <summary>A bool metadata field.</summary>
    [BsonElement("parking_is_included")]
    [VectorStoreData]
    public bool ParkingIncluded { get; set; }

    /// <summary>An array metadata field.</summary>
    [VectorStoreData]
    public List<string> Tags { get; set; } = [];

    /// <summary>A data field.</summary>
    [VectorStoreData]
    public string? Description { get; set; }

    /// <summary>A vector field.</summary>
    [VectorStoreVector(Dimensions: 4, DistanceFunction = DistanceFunction.CosineDistance, IndexKind = IndexKind.IvfFlat)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
