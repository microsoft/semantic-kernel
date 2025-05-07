// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

/// <summary>
/// Tests CRUD operations using a model without a vector.
/// This is only supported by a subset of databases so only extend if applicable for your database.
/// </summary>
public class NoVectorConformanceTests<TKey>(NoVectorConformanceTests<TKey>.Fixture fixture) where TKey : notnull
{
    [ConditionalFact]
    public Task GetAsyncReturnsInsertedRecord_WithVectors()
        => this.GetAsyncReturnsInsertedRecord(includeVectors: true);

    [ConditionalFact]
    public Task GetAsyncReturnsInsertedRecord_WithoutVectors()
        => this.GetAsyncReturnsInsertedRecord(includeVectors: false);

    private async Task GetAsyncReturnsInsertedRecord(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var received = await fixture.Collection.GetAsync(expectedRecord.Id, new() { IncludeVectors = includeVectors });

        expectedRecord.AssertEqual(received);
    }

    [ConditionalFact]
    public Task UpsertAsyncCanInsertNewRecord_WithVectors()
        => this.UpsertAsyncCanInsertNewRecord(includeVectors: true);

    [ConditionalFact]
    public Task UpsertAsyncCanInsertNewRecord_WithoutVectors()
        => this.UpsertAsyncCanInsertNewRecord(includeVectors: false);

    private async Task UpsertAsyncCanInsertNewRecord(bool includeVectors)
    {
        var collection = fixture.Collection;
        TKey expectedKey = fixture.GenerateNextKey<TKey>();
        NoVectorRecord inserted = new()
        {
            Id = expectedKey,
            Text = "some"
        };

        Assert.Null(await collection.GetAsync(expectedKey));
        TKey key = await collection.UpsertAsync(inserted);
        Assert.Equal(expectedKey, key);

        var received = await collection.GetAsync(expectedKey, new() { IncludeVectors = includeVectors });
        inserted.AssertEqual(received);
    }

    [ConditionalFact]
    public Task UpsertAsyncCanUpdateExistingRecord_WithVectors()
        => this.UpsertAsyncCanUpdateExistingRecord(includeVectors: true);

    [ConditionalFact]
    public Task UpsertAsyncCanUpdateExistingRecord__WithoutVectors()
        => this.UpsertAsyncCanUpdateExistingRecord(includeVectors: false);

    private async Task UpsertAsyncCanUpdateExistingRecord(bool includeVectors)
    {
        var collection = fixture.Collection;
        var existingRecord = fixture.TestData[1];
        NoVectorRecord updated = new()
        {
            Id = existingRecord.Id,
            Text = "updated"
        };

        Assert.NotNull(await collection.GetAsync(existingRecord.Id));
        TKey key = await collection.UpsertAsync(updated);
        Assert.Equal(existingRecord.Id, key);

        var received = await collection.GetAsync(existingRecord.Id, new() { IncludeVectors = includeVectors });
        updated.AssertEqual(received);
    }

    [ConditionalFact]
    public async Task DeleteAsyncDeletesTheRecord()
    {
        var recordToRemove = fixture.TestData[2];

        Assert.NotNull(await fixture.Collection.GetAsync(recordToRemove.Id));
        await fixture.Collection.DeleteAsync(recordToRemove.Id);
        Assert.Null(await fixture.Collection.GetAsync(recordToRemove.Id));
    }

    /// <summary>
    /// This class is for testing databases that support having no vector.
    /// Not all DBs support this.
    /// </summary>
    public sealed class NoVectorRecord
    {
        public const int DimensionCount = 3;

        [VectorStoreRecordKey(StoragePropertyName = "key")]
        public TKey Id { get; set; } = default!;

        [VectorStoreRecordData(StoragePropertyName = "text")]
        public string? Text { get; set; }

        public void AssertEqual(NoVectorRecord? other)
        {
            Assert.NotNull(other);
            Assert.Equal(this.Id, other.Id);
            Assert.Equal(this.Text, other.Text);
        }
    }

    /// <summary>
    /// Provides data and configuration for a model without a vector, which is supported by some connectors.
    /// </summary>
    public abstract class Fixture : VectorStoreCollectionFixture<TKey, NoVectorRecord>
    {
        protected override List<NoVectorRecord> BuildTestData() =>
        [
            new()
            {
                Id = this.GenerateNextKey<TKey>(),
                Text = "UsedByGetTests",
            },
            new()
            {
                Id = this.GenerateNextKey<TKey>(),
                Text = "UsedByUpdateTests",
            },
            new()
            {
                Id = this.GenerateNextKey<TKey>(),
                Text = "UsedByDeleteTests",
            },
            new()
            {
                Id = this.GenerateNextKey<TKey>(),
                Text = "UsedByDeleteBatchTests",
            }
        ];

        public override VectorStoreRecordDefinition GetRecordDefinition()
            => new()
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty(nameof(NoVectorRecord.Id), typeof(TKey)) { StoragePropertyName = "key" },
                    new VectorStoreRecordDataProperty(nameof(NoVectorRecord.Text), typeof(string)) { IsIndexed = true, StoragePropertyName = "text" },
                ]
            };

        protected override async Task WaitForDataAsync()
        {
            for (var i = 0; i < 20; i++)
            {
                var results = await this.Collection.GetAsync([this.TestData[0].Id, this.TestData[1].Id, this.TestData[2].Id, this.TestData[3].Id]).ToArrayAsync();
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
