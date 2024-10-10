// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Data;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBNoSQL;

#pragma warning disable CS8618

public record AzureCosmosDBNoSQLHotel()
{
    /// <summary>The key of the record.</summary>
    [VectorStoreRecordKey]
    public string HotelId { get; init; }

    /// <summary>A string metadata field.</summary>
    [VectorStoreRecordData(IsFilterable = true)]
    public string? HotelName { get; set; }

    /// <summary>An int metadata field.</summary>
    [VectorStoreRecordData(IsFullTextSearchable = true)]
    public int HotelCode { get; set; }

    /// <summary>A float metadata field.</summary>
    [VectorStoreRecordData]
    public float? HotelRating { get; set; }

    /// <summary>A bool metadata field.</summary>
    [JsonPropertyName("parking_is_included")]
    [VectorStoreRecordData]
    public bool ParkingIncluded { get; set; }

    /// <summary>An array metadata field.</summary>
    [VectorStoreRecordData]
    public List<string> Tags { get; set; } = [];

    /// <summary>A data field.</summary>
    [VectorStoreRecordData]
    public string Description { get; set; }

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// <summary>A datetime field.</summary>
    [VectorStoreRecordData]
    public DateTimeOffset Timestamp { get; set; }

<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    /// <summary>A vector field.</summary>
    [VectorStoreRecordVector(Dimensions: 4, IndexKind: IndexKind.Flat, DistanceFunction: DistanceFunction.CosineSimilarity)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
}
