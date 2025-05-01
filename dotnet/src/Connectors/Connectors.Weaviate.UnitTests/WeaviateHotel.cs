// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

#pragma warning disable CS8618

public sealed record WeaviateHotel
{
    /// <summary>The key of the record.</summary>
    [VectorStoreKeyProperty]
    public Guid HotelId { get; init; }

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
    [JsonPropertyName("parking_is_included")]
    [VectorStoreDataProperty]
    public bool ParkingIncluded { get; set; }

    /// <summary>An array metadata field.</summary>
    [VectorStoreDataProperty]
    public List<string> Tags { get; set; } = [];

    /// <summary>A data field.</summary>
    [VectorStoreDataProperty(IsFullTextIndexed = true)]
    public string Description { get; set; }

    [VectorStoreDataProperty]
    public DateTimeOffset Timestamp { get; set; }

    /// <summary>A vector field.</summary>
    [VectorStoreVectorProperty(Dimensions: 4, DistanceFunction = DistanceFunction.CosineDistance, IndexKind = IndexKind.Hnsw)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
