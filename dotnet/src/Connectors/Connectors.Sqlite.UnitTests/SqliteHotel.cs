// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

public class SqliteHotel<TKey>()
{
    /// <summary>The key of the record.</summary>
    [VectorStoreRecordKey]
    public TKey? HotelId { get; init; }

    /// <summary>A string metadata field.</summary>
    [VectorStoreRecordData(IsIndexed = true)]
    public string? HotelName { get; set; }

    /// <summary>An int metadata field.</summary>
    [VectorStoreRecordData]
    public int HotelCode { get; set; }

    /// <summary>A float metadata field.</summary>
    [VectorStoreRecordData]
    public float? HotelRating { get; set; }

    /// <summary>A bool metadata field.</summary>
    [VectorStoreRecordData(StoragePropertyName = "parking_is_included")]
    public bool ParkingIncluded { get; set; }

    /// <summary>A data field.</summary>
    [VectorStoreRecordData]
    public string? Description { get; set; }

    /// <summary>A vector field.</summary>
    [VectorStoreRecordVector(Dimensions: 4, DistanceFunction = DistanceFunction.EuclideanDistance)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
