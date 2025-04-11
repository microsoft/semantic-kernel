// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Postgres;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.

/// <summary>
/// A test model for the postgres vector store.
/// </summary>
public record PostgresHotel<T>()
{
    /// <summary>The key of the record.</summary>
    [VectorStoreRecordKey]
    public T HotelId { get; init; }

    /// <summary>A string metadata field.</summary>
    [VectorStoreRecordData()]
    public string? HotelName { get; set; }

    /// <summary>An int metadata field.</summary>
    [VectorStoreRecordData()]
    public int HotelCode { get; set; }

    /// <summary>A  float metadata field.</summary>
    [VectorStoreRecordData()]
    public float? HotelRating { get; set; }

    /// <summary>A bool metadata field.</summary>
    [VectorStoreRecordData(StoragePropertyName = "parking_is_included")]
    public bool ParkingIncluded { get; set; }

    [VectorStoreRecordData]
    public List<string> Tags { get; set; } = [];

    [VectorStoreRecordData]
    public List<int>? ListInts { get; set; } = null;

    /// <summary>A data field.</summary>
    [VectorStoreRecordData]
    public string Description { get; set; }

    /// <summary>A vector field.</summary>
    [VectorStoreRecordVector(Dimensions: 4, DistanceFunction = DistanceFunction.EuclideanDistance, IndexKind = IndexKind.Hnsw)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public DateTimeOffset UpdatedAt { get; set; } = DateTimeOffset.UtcNow;

    public PostgresHotel(T key) : this()
    {
        this.HotelId = key;
    }
}

#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
