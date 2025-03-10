// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

public abstract class BatchConformanceTests<TKey>(VectorStoreFixture fixture)
    : ConformanceTestsBase<TKey, SimpleModel<TKey>>(fixture) where TKey : notnull
{
    [ConditionalFact]
    public async Task UpsertBatchAsync_EmptyBatch_DoesNotThrow()
    {
        await this.ExecuteAsync(async collection =>
        {
            Assert.Empty(await collection.UpsertBatchAsync([]).ToArrayAsync());
        });
    }

    [ConditionalFact]
    public async Task DeleteBatchAsync_EmptyBatch_DoesNotThrow()
    {
        await this.ExecuteAsync(async collection =>
        {
            await collection.DeleteBatchAsync([]);
        });
    }

    [ConditionalFact]
    public async Task GetBatchAsync_EmptyBatch_DoesNotThrow()
    {
        await this.ExecuteAsync(async collection =>
        {
            Assert.Empty(await collection.GetBatchAsync([]).ToArrayAsync());
        });
    }

    [ConditionalFact]
    public async Task UpsertBatchAsync_NullBatch_ThrowsArgumentNullException()
    {
        await this.ExecuteAsync(async collection =>
        {
            ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => collection.UpsertBatchAsync(records: null!).ToArrayAsync().AsTask());
            Assert.Equal("records", ex.ParamName);
        });
    }

    [ConditionalFact]
    public async Task DeleteBatchAsync_NullKeys_ThrowsArgumentNullException()
    {
        await this.ExecuteAsync(async collection =>
        {
            ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => collection.DeleteBatchAsync(keys: null!));
            Assert.Equal("keys", ex.ParamName);
        });
    }

    [ConditionalFact]
    public async Task GetBatchAsync_NullKeys_ThrowsArgumentNullException()
    {
        await this.ExecuteAsync(async collection =>
        {
            ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => collection.GetBatchAsync(keys: null!).ToArrayAsync().AsTask());
            Assert.Equal("keys", ex.ParamName);
        });
    }

    [ConditionalFact]
    public Task CanInsertUpdateAndDelete_WithVectors()
        => this.CanInsertUpdateAndDelete(includeVectors: true);

    [ConditionalFact]
    public Task CanInsertUpdateAndDelete_WithoutVectors()
        => this.CanInsertUpdateAndDelete(includeVectors: false);

    private async Task CanInsertUpdateAndDelete(bool includeVectors)
    {
        await this.ExecuteAsync(async collection =>
        {
            SimpleModel<TKey>[] inserted = Enumerable.Range(0, 10).Select(i => new SimpleModel<TKey>()
            {
                Id = this.Fixture.GenerateNextKey<TKey>(),
                Number = 100 + i,
                Text = i.ToString(),
                Floats = Enumerable.Range(0, 10).Select(j => (float)(i + j)).ToArray()
            }).ToArray();

            TKey[] keys = await collection.UpsertBatchAsync(inserted).ToArrayAsync();
            Assert.Equal(
                inserted.Select(r => r.Id).OrderBy(id => id).ToArray(),
                keys.OrderBy(id => id).ToArray());

            SimpleModel<TKey>[] received = await collection.GetBatchAsync(keys, new() { IncludeVectors = includeVectors }).ToArrayAsync();
            for (int i = 0; i < inserted.Length; i++)
            {
                this.AssertEqual(inserted[i], this.GetRecord(received, inserted[i].Id!), includeVectors);
            }

            SimpleModel<TKey>[] updated = inserted.Select(i => new SimpleModel<TKey>()
            {
                Id = i.Id,
                Text = i.Text + "updated",
                Number = i.Number + 200,
                Floats = i.Floats
            }).ToArray();

            keys = await collection.UpsertBatchAsync(updated).ToArrayAsync();
            Assert.Equal(
                updated.Select(r => r.Id).OrderBy(id => id).ToArray(),
                keys.OrderBy(id => id).ToArray());

            received = await collection.GetBatchAsync(keys, new() { IncludeVectors = includeVectors }).ToArrayAsync();
            for (int i = 0; i < updated.Length; i++)
            {
                this.AssertEqual(updated[i], this.GetRecord(received, updated[i].Id!), includeVectors);
            }

            await collection.DeleteBatchAsync(keys);

            Assert.False(await collection.GetBatchAsync(keys).AnyAsync());
        });
    }

    // The order of records in the received array is not guaranteed
    // to match the order of keys in the requested keys array.
    private SimpleModel<TKey> GetRecord(SimpleModel<TKey>[] received, TKey key)
        => received.Single(r => r.Id!.Equals(key));
}
