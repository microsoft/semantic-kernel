// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Microsoft.Extensions.VectorData;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

#pragma warning disable CS8618

public class AzureAISearchHotel
{
    [SimpleField(IsKey = true, IsFilterable = true)]
    [VectorStoreKeyProperty]
    public string HotelId { get; set; }

    [SearchableField(IsFilterable = true, IsSortable = true)]
    [VectorStoreDataProperty(IsIndexed = true, IsFullTextIndexed = true)]
    public string HotelName { get; set; }

    [SearchableField(AnalyzerName = LexicalAnalyzerName.Values.EnLucene)]
    [VectorStoreDataProperty]
    public string Description { get; set; }

    [VectorStoreVectorProperty(1536)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }

    [SearchableField(IsFilterable = true, IsFacetable = true)]
    [VectorStoreDataProperty(IsIndexed = true)]
#pragma warning disable CA1819 // Properties should not return arrays
    public string[] Tags { get; set; }
#pragma warning restore CA1819 // Properties should not return arrays

    [JsonPropertyName("parking_is_included")]
    [SimpleField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
    [VectorStoreDataProperty(IsIndexed = true)]
    public bool? ParkingIncluded { get; set; }

    [SimpleField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
    [VectorStoreDataProperty(IsIndexed = true)]
    public DateTimeOffset? LastRenovationDate { get; set; }

    [SimpleField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
    [VectorStoreDataProperty]
    public double? Rating { get; set; }
}
