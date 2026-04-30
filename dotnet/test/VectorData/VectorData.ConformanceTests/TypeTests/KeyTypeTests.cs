// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests.TypeTests;

public abstract class KeyTypeTests(KeyTypeTests.Fixture fixture)
{
    // All MEVD providers are expected to support Guid keys (possibly by storing them as strings), including
    // auto-generation.
    // This allows upper layers such as Microsoft.Extensions.DataIngestion to use Guid keys consistently.
    [ConditionalFact]
    public virtual Task Guid()
        => this.Test<Guid>(
            new Guid("603840bf-cf91-4521-8b8e-8b6a2e75910a"),
            supportsAutoGeneration: true);

    /// <summary>
    /// Verifies that creating a collection with a TKey that doesn't match the key property type on the model throws.
    /// </summary>
    [ConditionalFact]
    public virtual void MismatchedKeyTypeThrows()
    {
        // The definition says the key property is string (matching Record<string>.Key),
        // but TKey is Guid - this mismatch should be detected during model building.
        Assert.Throws<InvalidOperationException>(() =>
            fixture.TestStore.CreateCollection<Guid, Record<string>>(
                fixture.CollectionName, fixture.CreateRecordDefinition<string>(withAutoGeneration: false)));
    }

    protected virtual Task Test<TKey>(TKey key, bool supportsAutoGeneration = false)
        where TKey : struct
        => this.Test<TKey>(key, default!, supportsAutoGeneration: supportsAutoGeneration);

    // Note that we do not currently support testing auto generation for reference types, since
    // no such case currently exists in a known provider. As a result we require a second key
    // value.
    protected virtual Task Test<TKey>(TKey key1, TKey key2)
        where TKey : class
        => this.Test<TKey>(key1, key2, supportsAutoGeneration: false);

    protected virtual async Task Test<TKey>(
        TKey key1,
        TKey key2,
        bool supportsAutoGeneration = false)
        where TKey : notnull
    {
        Assert.NotEqual(key1, key2);

        using var collection = fixture.CreateCollection<TKey>(withAutoGeneration: false);

        {
            await collection.EnsureCollectionDeletedAsync();
            await collection.EnsureCollectionExistsAsync();

            var record = new Record<TKey>
            {
                Key = key1,
                Int = 8,
                Vector = new ReadOnlyMemory<float>([1, 2, 3])
            };

            var nextRecord = new Record<TKey>
            {
                Key = key2,
                Int = 9,
                Vector = new ReadOnlyMemory<float>([3, 2, 1])
            };

            await collection.UpsertAsync(record);
            // Exercise multi-record plus updating existing record
            await collection.UpsertAsync([record, nextRecord]);
            await fixture.TestStore.WaitForDataAsync(collection, recordCount: 2);

            // Single record get
            var result = await collection.GetAsync(key1);
            Assert.NotNull(result);
            Assert.Equal(key1, result.Key);
            Assert.Equal(8, result.Int);

            // Multiple record get
            // Also ensures that the second record - with the default key value - got properly inserted and did not trigger auto-generation
            // (as we haven't configured it).
            var results = await collection.GetAsync([key1, key2]).ToListAsync();
            Assert.Equal(2, results.Count);
            var firstRecord = Assert.Single(results, r => r.Key.Equals(key1));
            Assert.Equal(8, firstRecord.Int);
            var secondRecord = Assert.Single(results, r => r.Key.Equals(key2));
            Assert.Equal(9, secondRecord.Int);
        }

        ///////////////////////
        // Test dynamic mapping
        ///////////////////////
        await collection.DeleteAsync(key1);
        await collection.DeleteAsync([key1, key2]);
        await fixture.TestStore.WaitForDataAsync(collection, recordCount: 0);

        using (var dynamicCollection = fixture.CreateDynamicCollection<TKey>(withAutoGeneration: false))
        {
            await dynamicCollection.EnsureCollectionExistsAsync();

            var dynamicRecord = new Dictionary<string, object?>
            {
                [nameof(Record<TKey>.Key)] = key1,
                [nameof(Record<TKey>.Int)] = 8,
                [nameof(Record<TKey>.Vector)] = new ReadOnlyMemory<float>([1, 2, 3])
            };
            var nextDynamicRecord = new Dictionary<string, object?>
            {
                [nameof(Record<TKey>.Key)] = key2,
                [nameof(Record<TKey>.Int)] = 9,
                [nameof(Record<TKey>.Vector)] = new ReadOnlyMemory<float>([3, 2, 1])
            };

            await dynamicCollection.UpsertAsync(dynamicRecord);
            // Exercise multi-record plus updating existing record
            await dynamicCollection.UpsertAsync([dynamicRecord, nextDynamicRecord]);
            await fixture.TestStore.WaitForDataAsync(dynamicCollection, recordCount: 2);

            // Single record get
            var dynamicResult = await dynamicCollection.GetAsync(key1);
            Assert.NotNull(dynamicResult);
            Assert.IsType<TKey>(dynamicResult[nameof(Record<TKey>.Key)]);
            Assert.Equal(key1, (TKey)dynamicResult[nameof(Record<TKey>.Key)]!);
            Assert.Equal(8, dynamicResult[nameof(Record<TKey>.Int)]);

            // Multiple record get
            // Also ensures that the second record - with the default key value - got properly inserted and did not trigger auto-generation
            // (as we haven't configured it).
            var dynamicResults = await dynamicCollection.GetAsync([key1, key2]).ToListAsync();
            Assert.Equal(2, dynamicResults.Count);
            var firstDynamicRecord = Assert.Single(dynamicResults, r => r[nameof(Record<TKey>.Key)]!.Equals(key1));
            Assert.IsType<TKey>(firstDynamicRecord[nameof(Record<TKey>.Key)]);
            Assert.Equal(8, firstDynamicRecord[nameof(Record<TKey>.Int)]);
            var secondDynamicRecord = Assert.Single(dynamicResults, r => r[nameof(Record<TKey>.Key)]!.Equals(key2));
            Assert.IsType<TKey>(secondDynamicRecord[nameof(Record<TKey>.Key)]);
            Assert.Equal(9, secondDynamicRecord[nameof(Record<TKey>.Int)]);
        }

        if (supportsAutoGeneration)
        {
            // Above we tested with a collection where auto-generation isn't enabled - including with the default key value,
            // which would have triggered auto-generation if it was enabled.
            // Now, drop and recreate the collection with auto-generation enabled, and test that it works.
            await collection.EnsureCollectionDeletedAsync();

            // Pass null to test the provider's default behavior, which should be to enable auto-generation.
            using var collectionWithAutoGeneration = fixture.CreateCollection<TKey>(withAutoGeneration: null);
            await collectionWithAutoGeneration.EnsureCollectionExistsAsync();

            var record = new Record<TKey>
            {
                Key = key1,
                Int = 8,
                Vector = new ReadOnlyMemory<float>([1, 2, 3])
            };

            var recordWithDefaultValueKey1 = new Record<TKey>
            {
                Key = key2,
                Int = 9,
                Vector = new ReadOnlyMemory<float>([3, 2, 1])
            };

            var recordWithDefaultValueKey2 = new Record<TKey>
            {
                Key = key2,
                Int = 10,
                Vector = new ReadOnlyMemory<float>([3, 2, 1])
            };

            var recordWithDefaultValueKey3 = new Record<TKey>
            {
                Key = key2,
                Int = 11,
                Vector = new ReadOnlyMemory<float>([3, 2, 1])
            };

            // recordWithDefaultValueKey1 gets inserted alone, exercising single-record upsert with auto-generation.
            await collectionWithAutoGeneration.UpsertAsync(recordWithDefaultValueKey1);
            Assert.NotEqual(recordWithDefaultValueKey1.Key, key2);
            var preUpdateGeneratedKey = recordWithDefaultValueKey1.Key;
            recordWithDefaultValueKey1.Int = 99;

            // recordWithDefaultValueKey1 gets upserted, exercising update instead of insert.
            // recordWithDefaultValueKey2 and 3 get inserted, exercising multi-record upsert with auto-generation; we insert two records to make
            // sure the correct key gets injected back into each record.
            // Finally, record gets inserted with a non-generated key, to make sure auto-generation doesn't kick in for non-CLR-default keys.
            await collectionWithAutoGeneration.UpsertAsync([recordWithDefaultValueKey1, recordWithDefaultValueKey2, recordWithDefaultValueKey3, record]);
            await fixture.TestStore.WaitForDataAsync(collectionWithAutoGeneration, recordCount: 4);

            Assert.Equal(recordWithDefaultValueKey1.Key, preUpdateGeneratedKey);
            Assert.Equal(99, recordWithDefaultValueKey1.Int);
            Assert.NotEqual(recordWithDefaultValueKey2.Key, key2);
            Assert.NotEqual(recordWithDefaultValueKey3.Key, key2);
            Assert.NotEqual(recordWithDefaultValueKey2.Key, recordWithDefaultValueKey1.Key!);
            Assert.NotEqual(recordWithDefaultValueKey3.Key, recordWithDefaultValueKey1.Key!);
            Assert.NotEqual(recordWithDefaultValueKey3.Key, recordWithDefaultValueKey2.Key!);
            Assert.Equal(record.Key, key1);

            var results = await collectionWithAutoGeneration.GetAsync([key1, recordWithDefaultValueKey1.Key, recordWithDefaultValueKey2.Key, recordWithDefaultValueKey3.Key]).ToListAsync();
            Assert.Single(results, r => r.Key.Equals(recordWithDefaultValueKey1.Key));
            Assert.Single(results, r => r.Key.Equals(recordWithDefaultValueKey2.Key));
            Assert.Single(results, r => r.Key.Equals(recordWithDefaultValueKey3.Key));
            Assert.Single(results, r => r.Key.Equals(key1));
        }
        else
        {
            // Auto-generation is not supported for this type; ensure that model validation throws.
            Assert.Throws<NotSupportedException>(() => fixture.CreateCollection<TKey>(withAutoGeneration: true));
        }
    }

    public abstract class Fixture : VectorStoreFixture
    {
        protected virtual string CollectionNameBase => nameof(KeyTypeTests);
        public virtual string CollectionName => this.TestStore.AdjustCollectionName(this.CollectionNameBase);

        public virtual VectorStoreCollection<TKey, Record<TKey>> CreateCollection<TKey>(bool? withAutoGeneration)
            where TKey : notnull
            => this.TestStore.CreateCollection<TKey, Record<TKey>>(this.CollectionName, this.CreateRecordDefinition<TKey>(withAutoGeneration));

        public virtual VectorStoreCollection<object, Dictionary<string, object?>> CreateDynamicCollection<TKey>(bool withAutoGeneration)
            where TKey : notnull
            => this.TestStore.CreateDynamicCollection(this.CollectionName, this.CreateRecordDefinition<TKey>(withAutoGeneration));

        public virtual VectorStoreCollectionDefinition CreateRecordDefinition<TKey>(bool? withAutoGeneration)
            where TKey : notnull
            => new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty("Key", typeof(TKey)) { IsAutoGenerated = withAutoGeneration },
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
