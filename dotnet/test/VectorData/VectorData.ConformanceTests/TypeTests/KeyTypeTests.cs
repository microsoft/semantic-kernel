// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests.TypeTests;

public abstract class KeyTypeTests(KeyTypeTests.Fixture fixture)
{
    // All MEVD providers are expected to support Guid keys (possibly by storing them as strings).
    // This allows upper layers such as Microsoft.Extensions.DataIngestion to use Guid keys consistently.
    [ConditionalFact]
    public virtual Task Guid() => this.Test<Guid>(new Guid("603840bf-cf91-4521-8b8e-8b6a2e75910a"), new Guid("f507c6a2-43bd-4d8f-8656-890f2cdaf299"));

    protected virtual async Task Test<TKey>(TKey keyValue, TKey differentKey)
        where TKey : notnull
    {
        using var collection = fixture.CreateCollection<TKey>();

        await collection.EnsureCollectionDeletedAsync();
        await collection.EnsureCollectionExistsAsync();

        var record = new Record<TKey>
        {
            Key = keyValue,
            Int = 8,
            Vector = new ReadOnlyMemory<float>([1, 2, 3])
        };

        var nextRecord = new Record<TKey>
        {
            Key = differentKey,
            Int = 9,
            Vector = new ReadOnlyMemory<float>([3, 2, 1])
        };

        await collection.UpsertAsync(record);
        await collection.UpsertAsync([record, nextRecord]);
        await fixture.TestStore.WaitForDataAsync(collection, recordCount: 2);

        var result = await collection.GetAsync(keyValue);

        Assert.NotNull(result);
        Assert.Equal(keyValue, result.Key);
        Assert.Equal(8, result.Int);

        var results = await collection.GetAsync([keyValue, differentKey]).ToListAsync();

        Assert.Equal(2, results.Count);
        Assert.Equal(keyValue, results[0].Key);
        Assert.Equal(8, results[0].Int);
        Assert.Equal(differentKey, results[1].Key);
        Assert.Equal(9, results[1].Int);

        ///////////////////////
        // Test dynamic mapping
        ///////////////////////
        await collection.DeleteAsync(keyValue);
        await collection.DeleteAsync([keyValue, differentKey]);
        await fixture.TestStore.WaitForDataAsync(collection, recordCount: 0);

        using var dynamicCollection = fixture.CreateDynamicCollection<TKey>();
        await dynamicCollection.EnsureCollectionExistsAsync();

        var dynamicRecord = new Dictionary<string, object?>
        {
            [nameof(Record<TKey>.Key)] = keyValue,
            [nameof(Record<TKey>.Int)] = 8,
            [nameof(Record<TKey>.Vector)] = new ReadOnlyMemory<float>([1, 2, 3])
        };
        var nextDynamicRecord = new Dictionary<string, object?>
        {
            [nameof(Record<TKey>.Key)] = differentKey,
            [nameof(Record<TKey>.Int)] = 9,
            [nameof(Record<TKey>.Vector)] = new ReadOnlyMemory<float>([3, 2, 1])
        };

        await dynamicCollection.UpsertAsync(dynamicRecord);
        await dynamicCollection.UpsertAsync([dynamicRecord, nextDynamicRecord]);
        await fixture.TestStore.WaitForDataAsync(dynamicCollection, recordCount: 2);

        var dynamicResult = await dynamicCollection.GetAsync(keyValue);

        Assert.NotNull(dynamicResult);
        Assert.IsType<TKey>(dynamicResult[nameof(Record<TKey>.Key)]);
        Assert.Equal(keyValue, (TKey)dynamicResult[nameof(Record<TKey>.Key)]!);
        Assert.Equal(8, dynamicResult[nameof(Record<TKey>.Int)]);

        var dynamicResults = await dynamicCollection.GetAsync([keyValue, differentKey]).ToListAsync();
        Assert.Equal(2, dynamicResults.Count);
        Assert.IsType<TKey>(dynamicResults[0][nameof(Record<TKey>.Key)]);
        Assert.Equal(keyValue, (TKey)dynamicResults[0][nameof(Record<TKey>.Key)]!);
        Assert.Equal(8, dynamicResults[0][nameof(Record<TKey>.Int)]);
        Assert.IsType<TKey>(dynamicResults[1][nameof(Record<TKey>.Key)]);
        Assert.Equal(differentKey, (TKey)dynamicResults[1][nameof(Record<TKey>.Key)]!);
        Assert.Equal(9, dynamicResults[1][nameof(Record<TKey>.Int)]);
    }

    public abstract class Fixture : VectorStoreFixture
    {
        protected virtual string CollectionNameBase => nameof(KeyTypeTests);
        public virtual string CollectionName => this.TestStore.AdjustCollectionName(this.CollectionNameBase);

        public virtual VectorStoreCollection<TKey, Record<TKey>> CreateCollection<TKey>()
            where TKey : notnull
            => this.TestStore.DefaultVectorStore.GetCollection<TKey, Record<TKey>>(this.CollectionName, this.CreateRecordDefinition<TKey>());

        public virtual VectorStoreCollection<object, Dictionary<string, object?>> CreateDynamicCollection<TKey>()
            where TKey : notnull
            => this.TestStore.DefaultVectorStore.GetDynamicCollection(this.CollectionName, this.CreateRecordDefinition<TKey>());

        public virtual VectorStoreCollectionDefinition CreateRecordDefinition<TKey>()
            where TKey : notnull
            => new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty("Key", typeof(TKey)),
                    new VectorStoreDataProperty("Int", typeof(int)),
                    new VectorStoreVectorProperty("Vector", typeof(ReadOnlyMemory<float>), dimensions: 3)
                    {
                        DistanceFunction = this.DefaultDistanceFunction,
                        IndexKind = this.DefaultIndexKind
                    }
                ]
            };
    }

    public class Record<TKey>
    {
        public TKey Key { get; set; } = default!;
        public int Int { get; set; }
        public ReadOnlyMemory<float> Vector { get; set; }
    }
}
