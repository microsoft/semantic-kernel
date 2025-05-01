// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Sqlite;

public record SqliteHotel<TKey>()
{
    /// <summary>The key of the record.</summary>
    [VectorStoreKeyProperty]
    public TKey? HotelId { get; init; }

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
    [VectorStoreDataProperty(StoragePropertyName = "parking_is_included")]
    public bool ParkingIncluded { get; set; }

    /// <summary>A data field.</summary>
    [VectorStoreDataProperty]
    public string? Description { get; set; }

    /// <summary>A vector field.</summary>
    [VectorStoreVectorProperty(Dimensions: 4, DistanceFunction = DistanceFunction.EuclideanDistance)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
