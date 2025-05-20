// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Redis;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.

/// <summary>
/// A test model for the vector store that has complex properties as supported by JSON redis mode.
/// </summary>
public class RedisHotel
{
    [VectorStoreKey]
    public string HotelId { get; init; }

    [VectorStoreData(IsIndexed = true)]
    public string HotelName { get; init; }

    [VectorStoreData(IsIndexed = true)]
    public int HotelCode { get; init; }

    [VectorStoreData(IsFullTextIndexed = true)]
    public string Description { get; init; }

    [VectorStoreVector(4)]
    public ReadOnlyMemory<float>? DescriptionEmbedding { get; init; }

#pragma warning disable CA1819 // Properties should not return arrays
    [VectorStoreData(IsIndexed = true)]
    public string[] Tags { get; init; }

    [VectorStoreData(IsFullTextIndexed = true)]
    public string[] FTSTags { get; init; }
#pragma warning restore CA1819 // Properties should not return arrays

    [JsonPropertyName("parking_is_included")]
    [VectorStoreData(StorageName = "parking_is_included")]
    public bool ParkingIncluded { get; init; }

    [VectorStoreData]
    public DateTimeOffset LastRenovationDate { get; init; }

    [VectorStoreData]
    public double Rating { get; init; }

    [VectorStoreData]
    public RedisHotelAddress Address { get; init; }
}

/// <summary>
/// A test model for the vector store to simulate a complex type.
/// </summary>
public class RedisHotelAddress
{
    public string City { get; init; }
    public string Country { get; init; }
}

/// <summary>
/// A test model for the vector store that only uses basic types as supported by HashSets Redis mode.
/// </summary>
public class RedisBasicHotel<TVectorElement>
{
    [VectorStoreKey]
    public string HotelId { get; init; }

    [VectorStoreData(IsIndexed = true)]
    public string HotelName { get; init; }

    [VectorStoreData(IsIndexed = true)]
    public int HotelCode { get; init; }

    [VectorStoreData(IsFullTextIndexed = true)]
    public string Description { get; init; }

    [VectorStoreVector(4)]
    public ReadOnlyMemory<TVectorElement>? DescriptionEmbedding { get; init; }

    [JsonPropertyName("parking_is_included")]
    [VectorStoreData(StorageName = "parking_is_included")]
    public bool ParkingIncluded { get; init; }

    [VectorStoreData]
    public double Rating { get; init; }
}

/// <summary>
/// A test model for the vector store that only uses basic types as supported by HashSets Redis mode.
/// </summary>
public class RedisBasicFloat32Hotel : RedisBasicHotel<float>
{
}

/// <summary>
/// A test model for the vector store that only uses basic types as supported by HashSets Redis mode.
/// </summary>
public class RedisBasicFloat64Hotel : RedisBasicHotel<double>
{
}
