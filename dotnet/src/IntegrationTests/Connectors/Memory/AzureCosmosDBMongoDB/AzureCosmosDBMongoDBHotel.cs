// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;

namespace SemanticKernel.IntegrationTests.Connectors.AzureCosmosDBMongoDB;

#pragma warning disable CS8618

public class AzureCosmosDBMongoDBHotel
{
    /// <summary>The key of the record.</summary>
    [VectorStoreKeyProperty]
    public string HotelId { get; init; }

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

    /// <summary>An array metadata field.</summary>
    [VectorStoreDataProperty]
    public List<string> Tags { get; set; } = [];

    /// <summary>A data field.</summary>
    [VectorStoreDataProperty]
    public string Description { get; set; }

    /// <summary>A datetime metadata field.</summary>
    [VectorStoreDataProperty]
    public DateTime Timestamp { get; set; }

    /// <summary>A vector field.</summary>
    [VectorStoreVectorProperty(Dimensions: 4, DistanceFunction = DistanceFunction.CosineDistance, IndexKind = IndexKind.IvfFlat)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
