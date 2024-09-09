// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Data;

namespace SemanticKernel.Connectors.AzureCosmosDBMongoDB.UnitTests;

public class AzureCosmosDBMongoDBHotelModel(string hotelId)
{
    /// <summary>The key of the record.</summary>
    [VectorStoreRecordKey]
    public string HotelId { get; init; } = hotelId;

    /// <summary>A string metadata field.</summary>
    [VectorStoreRecordData]
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

    /// <summary>An array metadata field.</summary>
    [VectorStoreRecordData]
    public List<string> Tags { get; set; } = [];

    /// <summary>A data field.</summary>
    [VectorStoreRecordData]
    public string? Description { get; set; }

    /// <summary>A vector field.</summary>
    [VectorStoreRecordVector(Dimensions: 4, IndexKind: IndexKind.IvfFlat, DistanceFunction: DistanceFunction.CosineDistance)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
