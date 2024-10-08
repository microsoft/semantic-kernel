// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Data;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
public record PineconeHotel()
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
{
    [VectorStoreRecordKey]
    public string HotelId { get; init; }

    [VectorStoreRecordData]
    public string HotelName { get; set; }

    [JsonPropertyName("code_of_the_hotel")]
    [VectorStoreRecordData]
    public int HotelCode { get; set; }

    [VectorStoreRecordData]
    public float HotelRating { get; set; }

    [JsonPropertyName("json_parking")]
    [VectorStoreRecordData(StoragePropertyName = "parking_is_included")]
    public bool ParkingIncluded { get; set; }

    [VectorStoreRecordData]
    public List<string> Tags { get; set; } = [];

    [VectorStoreRecordData]
    public string Description { get; set; }

    [VectorStoreRecordVector(Dimensions: 8, IndexKind: null, DistanceFunction: DistanceFunction.DotProductSimilarity)]
    public ReadOnlyMemory<float> DescriptionEmbedding { get; set; }
}
