// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace CosmosNoSql.ConformanceTests;

[CosmosConnectionStringRequired]
public sealed class CosmosNoSqlCollectionOptionsTests(CosmosNoSqlCollectionOptionsTests.Fixture fixture)
    : IClassFixture<CosmosNoSqlCollectionOptionsTests.Fixture>
{
    [ConditionalFact]
    public async Task Collection_supports_partition_key_composite_key()
    {
        var store = (CosmosNoSqlTestStore)fixture.TestStore;
        var collectionName = fixture.TestStore.AdjustCollectionName("PartitionKeyCompositeKey");

        using VectorStoreCollection<CosmosNoSqlCompositeKey, PartitionedHotel> collection =
            new CosmosNoSqlCollection<CosmosNoSqlCompositeKey, PartitionedHotel>(
                store.Database,
                collectionName,
                new() { PartitionKeyPropertyName = nameof(PartitionedHotel.HotelName) });

        await collection.EnsureCollectionExistsAsync();

        try
        {
            var record = new PartitionedHotel
            {
                HotelId = "hotel-1",
                HotelName = "Hotel A",
                Description = "Partitioned",
                Embedding = new([1f, 2f, 3f])
            };

            await collection.UpsertAsync(record);
            var key = new CosmosNoSqlCompositeKey(record.HotelId, record.HotelName);

            var fetched = await collection.GetAsync(key, new() { IncludeVectors = true });
            Assert.NotNull(fetched);

            await collection.DeleteAsync(key);
            Assert.Null(await collection.GetAsync(key));
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }

    [ConditionalTheory]
    [InlineData(IndexingMode.Consistent)]
    [InlineData(IndexingMode.Lazy)]
    [InlineData(IndexingMode.None)]
    public async Task Collection_supports_indexing_mode(IndexingMode indexingMode)
    {
        var store = (CosmosNoSqlTestStore)fixture.TestStore;
        var collectionName = fixture.TestStore.AdjustCollectionName($"IndexingMode_{indexingMode}");

        using var collection = new CosmosNoSqlCollection<string, IndexingModeHotel>(
            store.Database,
            collectionName,
            new() { IndexingMode = indexingMode, Automatic = indexingMode != IndexingMode.None });

        await collection.EnsureCollectionExistsAsync();

        try
        {
            var record = new IndexingModeHotel
            {
                HotelId = "hotel-2",
                HotelName = "Hotel B",
                Embedding = new([1f, 0f, 0f])
            };

            await collection.UpsertAsync(record);
            var fetched = await collection.GetAsync(record.HotelId);

            Assert.NotNull(fetched);

            await collection.DeleteAsync(record.HotelId);
            Assert.Null(await collection.GetAsync(record.HotelId));
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }

    public sealed class Fixture : VectorStoreFixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }

    private sealed class PartitionedHotel
    {
        [VectorStoreKey]
        public string HotelId { get; set; } = string.Empty;

        [VectorStoreData]
        public string HotelName { get; set; } = string.Empty;

        [VectorStoreData]
        public string? Description { get; set; }

        [VectorStoreVector(Dimensions: 3)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }

    private sealed class IndexingModeHotel
    {
        [VectorStoreKey]
        public string HotelId { get; set; } = string.Empty;

        [VectorStoreData]
        public string HotelName { get; set; } = string.Empty;

        [VectorStoreVector(Dimensions: 3)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
}
