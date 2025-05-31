// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;

namespace SemanticKernel.Connectors.SqliteVec.UnitTests;

public class SqliteHotel<TKey>()
{
    /// <summary>The key of the record.</summary>
    [VectorStoreKey]
    public TKey? HotelId { get; init; }

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
    [VectorStoreData(StorageName = "parking_is_included")]
    public bool ParkingIncluded { get; set; }

    /// <summary>A data field.</summary>
    [VectorStoreData]
    public string? Description { get; set; }

    /// <summary>A vector field.</summary>
    [VectorStoreVector(Dimensions: 4, DistanceFunction = DistanceFunction.EuclideanDistance)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
