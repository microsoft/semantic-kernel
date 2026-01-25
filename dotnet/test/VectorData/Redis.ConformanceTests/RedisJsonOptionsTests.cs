// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using Redis.ConformanceTests.Support;
using StackExchange.Redis;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace Redis.ConformanceTests;

public sealed class RedisJsonOptionsTests(RedisJsonOptionsTests.Fixture fixture)
    : IClassFixture<RedisJsonOptionsTests.Fixture>
{
    [ConditionalFact]
    public async Task Json_collection_with_prefix_and_nested_address_roundtrips()
    {
        var store = (RedisTestStore)fixture.TestStore;
        var collectionName = fixture.TestStore.AdjustCollectionName("jsonoptions");

        var options = new RedisJsonCollectionOptions { PrefixCollectionNameToKeyNames = true };
        using var collection = new RedisJsonCollection<string, RedisJsonHotel>(store.Database, collectionName, options);

        await collection.EnsureCollectionExistsAsync();

        try
        {
            var record = new RedisJsonHotel
            {
                HotelId = "hotel-1",
                HotelName = "Test Hotel",
                ParkingIncluded = true,
                Address = new RedisAddress { City = "Seattle", Country = "USA" },
                DescriptionEmbedding = new([30f, 31f, 32f, 33f])
            };

            await collection.UpsertAsync(record);
            var fetched = await collection.GetAsync(record.HotelId, new() { IncludeVectors = true });

            Assert.NotNull(fetched);
            Assert.Equal(record.HotelId, fetched!.HotelId);
            Assert.Equal(record.HotelName, fetched.HotelName);
            Assert.Equal(record.ParkingIncluded, fetched.ParkingIncluded);
            Assert.NotNull(fetched.Address);
            Assert.Equal(record.Address.City, fetched.Address.City);
            Assert.Equal(record.Address.Country, fetched.Address.Country);
            Assert.Equal(record.DescriptionEmbedding.ToArray(), fetched.DescriptionEmbedding.ToArray());
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }

    [ConditionalFact]
    public async Task Json_collection_get_throws_for_invalid_schema()
    {
        var store = (RedisTestStore)fixture.TestStore;
        var collectionName = fixture.TestStore.AdjustCollectionName("jsoninvalidschema");

        var options = new RedisJsonCollectionOptions { PrefixCollectionNameToKeyNames = true };
        using var collection = new RedisJsonCollection<string, RedisJsonHotel>(store.Database, collectionName, options);

        await collection.EnsureCollectionExistsAsync();

        try
        {
            var invalidDocument = new
            {
                HotelId = "another-id",
                HotelName = "Invalid Hotel",
                ParkingIncluded = false,
                DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
                Address = new { City = "Seattle", Country = "USA" }
            };

            var key = (RedisKey)$"{collectionName}:invalid";
            var json = JsonSerializer.Serialize(invalidDocument);
            await store.Database.ExecuteAsync("JSON.SET", key, "$", json);

            await Assert.ThrowsAsync<InvalidOperationException>(async () =>
                await collection.GetAsync("invalid", new() { IncludeVectors = true }));
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }

    public sealed class Fixture : VectorStoreFixture
    {
        public override TestStore TestStore => RedisTestStore.JsonInstance;
    }

    private sealed class RedisJsonHotel
    {
        [VectorStoreKey]
        public string HotelId { get; set; } = string.Empty;

        [VectorStoreData(IsIndexed = true)]
        public string HotelName { get; set; } = string.Empty;

        [VectorStoreData(StorageName = "parking_is_included")]
        public bool ParkingIncluded { get; set; }

        [VectorStoreData]
        public RedisAddress Address { get; set; } = new();

        [VectorStoreVector(4)]
        public ReadOnlyMemory<float> DescriptionEmbedding { get; set; }
    }

    private sealed class RedisAddress
    {
        public string City { get; set; } = string.Empty;

        public string Country { get; set; } = string.Empty;
    }
}
