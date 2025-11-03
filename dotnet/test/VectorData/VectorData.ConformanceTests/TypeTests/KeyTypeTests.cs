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
    public virtual Task Guid() => this.Test<Guid>(new Guid("603840bf-cf91-4521-8b8e-8b6a2e75910a"));

    protected virtual async Task Test<TKey>(TKey mainValue)
        where TKey : notnull
    {
        using var collection = fixture.CreateCollection<TKey>();

        await collection.EnsureCollectionDeletedAsync();
        await collection.EnsureCollectionExistsAsync();

        var record = new Record<TKey>
        {
            Key = mainValue,
            Int = 8,
            Vector = new ReadOnlyMemory<float>([1, 2, 3])
        };

        await collection.UpsertAsync(record);
        await fixture.TestStore.WaitForDataAsync(collection, recordCount: 1);

        var result = await collection.GetAsync(mainValue);

        Assert.NotNull(result);
        Assert.Equal(8, result.Int);
    }

    public abstract class Fixture : VectorStoreFixture
    {
        public virtual string CollectionName => "KeyTypeTests";

        public virtual VectorStoreCollection<TKey, Record<TKey>> CreateCollection<TKey>()
            where TKey : notnull
            => this.TestStore.DefaultVectorStore.GetCollection<TKey, Record<TKey>>(this.CollectionName, this.CreateRecordDefinition<TKey>());

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
