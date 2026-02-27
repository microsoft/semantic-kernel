// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests;

public abstract class IndexKindTests<TKey>(IndexKindTests<TKey>.Fixture fixture)
    where TKey : notnull
{
    [ConditionalFact]
    public virtual Task Flat()
        => this.Test(IndexKind.Flat);

    protected virtual async Task Test(string indexKind)
    {
        using var collection = fixture.CreateCollection(indexKind);
        await collection.EnsureCollectionDeletedAsync();
        await collection.EnsureCollectionExistsAsync();

        SearchRecord[] records =
        [
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Int = 1,
                Vector = new([1, 2, 3]),
            },
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Int = 2,
                Vector = new([10, 30, 50]),
            },
            new()
            {
                Key = fixture.GenerateNextKey<TKey>(),
                Int = 3,
                Vector = new([100, 40, 70]),
            }
        ];

        await collection.UpsertAsync(records);

        await fixture.TestStore.WaitForDataAsync(collection, records.Length);

        var result = await collection.SearchAsync(new ReadOnlyMemory<float>([10, 30, 50]), top: 1).SingleAsync();

        Assert.NotNull(result);
        Assert.Equal(2, result.Record.Int);
    }

    public abstract class Fixture : VectorStoreFixture
    {
        protected virtual string CollectionNameBase => nameof(IndexKindTests<int>);
        public virtual string CollectionName => this.TestStore.AdjustCollectionName(this.CollectionNameBase);

        protected virtual string? DistanceFunction => null;

        public virtual VectorStoreCollection<TKey, SearchRecord> CreateCollection(string indexKind)
        {
            VectorStoreCollectionDefinition definition = new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty(nameof(SearchRecord.Key), typeof(TKey)),
                    new VectorStoreDataProperty(nameof(SearchRecord.Int), typeof(int)),
                    new VectorStoreVectorProperty(nameof(SearchRecord.Vector), typeof(ReadOnlyMemory<float>), dimensions: 3)
                    {
                        IndexKind = indexKind,
                        DistanceFunction = this.DistanceFunction ?? this.DefaultDistanceFunction
                    }
                ]
            };

            return this.TestStore.CreateCollection<TKey, SearchRecord>(this.CollectionName, definition);
        }
    }

    public class SearchRecord
    {
        public TKey Key { get; set; } = default!;
        public int Int { get; set; }
        public ReadOnlyMemory<float> Vector { get; set; }
    }
}
