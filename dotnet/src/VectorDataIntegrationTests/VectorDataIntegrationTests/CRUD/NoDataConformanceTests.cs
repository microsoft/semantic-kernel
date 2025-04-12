// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

/// <summary>
/// Tests CRUD operations using a model without data fields.
/// </summary>
public class NoDataConformanceTests<TKey>(NoDataConformanceTests<TKey>.Fixture fixture) where TKey : notnull
{
    [ConditionalFact]
    public virtual Task GetAsyncReturnsInsertedRecord_WithVectors()
        => this.GetAsyncReturnsInsertedRecord(includeVectors: true);

    [ConditionalFact]
    public virtual Task GetAsyncReturnsInsertedRecord_WithoutVectors()
        => this.GetAsyncReturnsInsertedRecord(includeVectors: false);

    private async Task GetAsyncReturnsInsertedRecord(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var received = await fixture.Collection.GetAsync(expectedRecord.Id, new() { IncludeVectors = includeVectors });

        expectedRecord.AssertEqual(received, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual Task UpsertAsyncCanInsertNewRecord_WithVectors()
        => this.UpsertAsyncCanInsertNewRecord(includeVectors: true);

    [ConditionalFact]
    public virtual Task UpsertAsyncCanInsertNewRecord_WithoutVectors()
        => this.UpsertAsyncCanInsertNewRecord(includeVectors: false);

    private async Task UpsertAsyncCanInsertNewRecord(bool includeVectors)
    {
        var collection = fixture.Collection;
        TKey expectedKey = fixture.GenerateNextKey<TKey>();
        NoDataRecord inserted = new()
        {
            Id = expectedKey,
            Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.1f, NoDataRecord.DimensionCount).ToArray())
        };

        Assert.Null(await collection.GetAsync(expectedKey));
        TKey key = await collection.UpsertAsync(inserted);
        Assert.Equal(expectedKey, key);

        var received = await collection.GetAsync(expectedKey, new() { IncludeVectors = includeVectors });
        inserted.AssertEqual(received, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual Task UpsertAsyncCanUpdateExistingRecord_WithVectors()
        => this.UpsertAsyncCanUpdateExistingRecord(includeVectors: true);

    [ConditionalFact]
    public virtual Task UpsertAsyncCanUpdateExistingRecord_WithoutVectors()
        => this.UpsertAsyncCanUpdateExistingRecord(includeVectors: false);

    private async Task UpsertAsyncCanUpdateExistingRecord(bool includeVectors)
    {
        var collection = fixture.Collection;
        var existingRecord = fixture.TestData[1];
        NoDataRecord updated = new()
        {
            Id = existingRecord.Id,
            Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.25f, NoDataRecord.DimensionCount).ToArray())
        };

        Assert.NotNull(await collection.GetAsync(existingRecord.Id, new() { IncludeVectors = true }));
        TKey key = await collection.UpsertAsync(updated);
        Assert.Equal(existingRecord.Id, key);

        var received = await collection.GetAsync(existingRecord.Id, new() { IncludeVectors = includeVectors });
        updated.AssertEqual(received, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task DeleteAsyncDeletesTheRecord()
    {
        var recordToRemove = fixture.TestData[2];

        Assert.NotNull(await fixture.Collection.GetAsync(recordToRemove.Id, new() { IncludeVectors = true }));
        await fixture.Collection.DeleteAsync(recordToRemove.Id);
        Assert.Null(await fixture.Collection.GetAsync(recordToRemove.Id));
    }

    /// <summary>
    /// This class is for testing databases that support having no data fields.
    /// </summary>
    public sealed class NoDataRecord
    {
        public const int DimensionCount = 3;

        [VectorStoreRecordKey(StoragePropertyName = "key")]
        public TKey Id { get; set; } = default!;

        [VectorStoreRecordVector(DimensionCount, StoragePropertyName = "embedding")]
        public ReadOnlyMemory<float> Floats { get; set; }

        public void AssertEqual(NoDataRecord? other, bool includeVectors, bool compareVectors)
        {
            Assert.NotNull(other);
            Assert.Equal(this.Id, other.Id);

            if (includeVectors)
            {
                Assert.Equal(this.Floats.Span.Length, other.Floats.Span.Length);

                if (compareVectors)
                {
                    Assert.True(this.Floats.Span.SequenceEqual(other.Floats.Span));
                }
            }
        }
    }

    /// <summary>
    /// Provides data and configuration for a model without data fields.
    /// </summary>
    public abstract class Fixture : VectorStoreCollectionFixture<TKey, NoDataRecord>
    {
        protected override List<NoDataRecord> BuildTestData() =>
        [
            new()
            {
                Id = this.GenerateNextKey<TKey>(),
                Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.1f, NoDataRecord.DimensionCount).ToArray())
            },
            new()
            {
                Id = this.GenerateNextKey<TKey>(),
                Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.2f, NoDataRecord.DimensionCount).ToArray())
            },
            new()
            {
                Id = this.GenerateNextKey<TKey>(),
                Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.3f, NoDataRecord.DimensionCount).ToArray())
            },
            new()
            {
                Id = this.GenerateNextKey<TKey>(),
                Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.4f, NoDataRecord.DimensionCount).ToArray())
            }
        ];

        public override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty(nameof(NoDataRecord.Id), typeof(TKey)) { StoragePropertyName = "key" },
                    new VectorStoreRecordVectorProperty(nameof(NoDataRecord.Floats), typeof(ReadOnlyMemory<float>), NoDataRecord.DimensionCount)
                    {
                        StoragePropertyName = "embedding",
                        IndexKind = this.IndexKind,
                    }
                ]
            };

        protected override async Task WaitForDataAsync()
        {
            for (var i = 0; i < 20; i++)
            {
                var getOptions = new GetRecordOptions { IncludeVectors = true };
                var results = await this.Collection.GetAsync([this.TestData[0].Id, this.TestData[1].Id, this.TestData[2].Id, this.TestData[3].Id], getOptions).ToArrayAsync();
                if (results.Length == 4 && results.All(r => r != null))
                {
                    return;
                }

                await Task.Delay(TimeSpan.FromMilliseconds(100));
            }

            throw new InvalidOperationException("Data did not appear in the collection within the expected time.");
        }
    }
}
