// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;

namespace SemanticKernel.Connectors.AzureCosmosDBNoSQL.UnitTests;

public class AzureCosmosDBNoSQLHotel(string hotelId)
{
    /// <summary>The key of the record.</summary>
    [VectorStoreKeyProperty]
    public string HotelId { get; init; } = hotelId;

    /// <summary>A string metadata field.</summary>
    [VectorStoreDataProperty]
    public string? HotelName { get; set; }

    /// <summary>An int metadata field.</summary>
    [VectorStoreDataProperty]
    public int HotelCode { get; set; }

    /// <summary>A float metadata field.</summary>
    [VectorStoreDataProperty]
    public float? HotelRating { get; set; }

    /// <summary>A bool metadata field.</summary>
    [VectorStoreDataProperty(StoragePropertyName = "parking_is_included")]
    public bool ParkingIncluded { get; set; }

    /// <summary>An array metadata field.</summary>
    [VectorStoreDataProperty]
    public List<string> Tags { get; set; } = [];

    /// <summary>A data field.</summary>
    [VectorStoreDataProperty]
    public string? Description { get; set; }

    /// <summary>A vector field.</summary>
    [JsonPropertyName("description_embedding")]
    [VectorStoreVectorProperty(Dimensions: 4, DistanceFunction = DistanceFunction.CosineSimilarity, IndexKind = IndexKind.Flat)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
