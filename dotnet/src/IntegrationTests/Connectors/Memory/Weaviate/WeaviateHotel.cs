// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Weaviate;

#pragma warning disable CS8618

public sealed record WeaviateHotel
{
    /// <summary>The key of the record.</summary>
    [VectorStoreRecordKey]
    public Guid HotelId { get; init; }

    /// <summary>A string metadata field.</summary>
    [VectorStoreRecordData(IsFilterable = true)]
    public string? HotelName { get; set; }

    /// <summary>An int metadata field.</summary>
    [VectorStoreRecordData(IsFilterable = true)]
    public int HotelCode { get; set; }

    /// <summary>A float metadata field.</summary>
    [VectorStoreRecordData(IsFilterable = true)]
    public float? HotelRating { get; set; }

    /// <summary>A bool metadata field.</summary>
    [JsonPropertyName("parking_is_included")]
    [VectorStoreRecordData(IsFilterable = true)]
    public bool ParkingIncluded { get; set; }

    /// <summary>An array metadata field.</summary>
    [VectorStoreRecordData(IsFilterable = true)]
    public List<string> Tags { get; set; } = [];

    /// <summary>A data field.</summary>
    [VectorStoreRecordData(IsFullTextSearchable = true, IsFilterable = true)]
    public string Description { get; set; }

    [VectorStoreRecordData(IsFilterable = true)]
    public DateTimeOffset Timestamp { get; set; }

    /// <summary>A vector field.</summary>
    [VectorStoreRecordVector(Dimensions: 4, DistanceFunction: DistanceFunction.CosineDistance, IndexKind: IndexKind.Hnsw)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
