// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

public abstract class BatchConformanceTests<TKey>(SimpleModelFixture<TKey> fixture) where TKey : notnull
{
    [ConditionalFact]
    public async Task GetBatchAsyncThrowsArgumentNullExceptionForNullKeys()
    {
        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => fixture.Collection.GetBatchAsync(keys: null!).ToArrayAsync().AsTask());
        Assert.Equal("keys", ex.ParamName);
    }

    [ConditionalFact]
    public async Task GetBatchAsyncDoesNotThrowForEmptyBatch()
    {
        Assert.Empty(await fixture.Collection.GetBatchAsync([]).ToArrayAsync());
    }

    [ConditionalFact]
    public Task GetBatchAsyncReturnsInsertedRecords_WithVectors()
        => this.GetBatchAsyncReturnsInsertedRecords(includeVectors: true);

    [ConditionalFact]
    public Task GetBatchAsyncReturnsInsertedRecords_WithoutVectors()
        => this.GetBatchAsyncReturnsInsertedRecords(includeVectors: false);

    private async Task GetBatchAsyncReturnsInsertedRecords(bool includeVectors)
    {
        var expectedRecords = fixture.TestData.Take(2); // the last two records can get deleted by other tests
        var ids = expectedRecords.Select(record => record.Id);

        var received = await fixture.Collection.GetBatchAsync(ids, new() { IncludeVectors = includeVectors }).ToArrayAsync();

        foreach (var record in expectedRecords)
        {
            record.AssertEqual(this.GetRecord(received, record.Id), includeVectors);
        }
    }

    [ConditionalFact]
    public async Task UpsertBatchAsyncThrowsArgumentNullExceptionForNullBatch()
    {
        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => fixture.Collection.UpsertBatchAsync(records: null!).ToArrayAsync().AsTask());
        Assert.Equal("records", ex.ParamName);
    }

    [ConditionalFact]
    public async Task UpsertBatchAsyncDoesNotThrowForEmptyBatch()
    {
        Assert.Empty(await fixture.Collection.UpsertBatchAsync([]).ToArrayAsync());
    }

    [ConditionalFact]
    public Task UpsertBatchAsyncCanInsertNewRecord_WithVectors()
        => this.UpsertBatchAsyncCanInsertNewRecords(includeVectors: true);

    [ConditionalFact]
    public Task UpsertBatchAsyncCanInsertNewRecord_WithoutVectors()
        => this.UpsertBatchAsyncCanInsertNewRecords(includeVectors: false);

    private async Task UpsertBatchAsyncCanInsertNewRecords(bool includeVectors)
    {
        var collection = fixture.Collection;
        SimpleModel<TKey>[] inserted = Enumerable.Range(0, 10).Select(i => new SimpleModel<TKey>()
        {
            Id = fixture.GenerateNextKey<TKey>(),
            Number = 100 + i,
            Text = i.ToString(),
            Floats = Enumerable.Range(0, SimpleModel<TKey>.DimensionCount).Select(j => (float)(i + j)).ToArray()
        }).ToArray();
        var keys = inserted.Select(record => record.Id).ToArray();

        Assert.Empty(await collection.GetBatchAsync(keys).ToArrayAsync());
        var receivedKeys = await collection.UpsertBatchAsync(inserted).ToArrayAsync();
        Assert.Equal(keys.ToHashSet(), receivedKeys.ToHashSet()); // .ToHashSet() to ignore order

        var received = await collection.GetBatchAsync(keys, new() { IncludeVectors = includeVectors }).ToArrayAsync();
        foreach (var record in inserted)
        {
            record.AssertEqual(this.GetRecord(received, record.Id), includeVectors);
        }
    }

    [ConditionalFact]
    public Task UpsertBatchAsyncCanUpdateExistingRecords_WithVectors()
        => this.UpsertBatchAsyncCanUpdateExistingRecords(includeVectors: true);

    [ConditionalFact]
    public Task UpsertBatchAsyncCanUpdateExistingRecords_WithoutVectors()
        => this.UpsertBatchAsyncCanUpdateExistingRecords(includeVectors: false);

    private async Task UpsertBatchAsyncCanUpdateExistingRecords(bool includeVectors)
    {
        SimpleModel<TKey>[] inserted = Enumerable.Range(0, 10).Select(i => new SimpleModel<TKey>()
        {
            Id = fixture.GenerateNextKey<TKey>(),
            Number = 100 + i,
            Text = i.ToString(),
            Floats = Enumerable.Range(0, SimpleModel<TKey>.DimensionCount).Select(j => (float)(i + j)).ToArray()
        }).ToArray();
        await fixture.Collection.UpsertBatchAsync(inserted).ToArrayAsync();

        SimpleModel<TKey>[] updated = inserted.Select(i => new SimpleModel<TKey>()
        {
            Id = i.Id,
            Text = i.Text + "updated",
            Number = i.Number + 200,
            Floats = i.Floats
        }).ToArray();

        var keys = await fixture.Collection.UpsertBatchAsync(updated).ToArrayAsync();
        Assert.Equal(
            updated.Select(r => r.Id).OrderBy(id => id).ToArray(),
            keys.OrderBy(id => id).ToArray());

        var received = await fixture.Collection.GetBatchAsync(keys, new() { IncludeVectors = includeVectors }).ToArrayAsync();
        foreach (var record in updated)
        {
            record.AssertEqual(this.GetRecord(received, record.Id), includeVectors);
        }
    }

    [ConditionalFact]
    public Task UpsertCanBothInsertAndUpdateRecordsFromTheSameBatch_WithVectors()
        => this.UpsertCanBothInsertAndUpdateRecordsFromTheSameBatch(includeVectors: true);

    [ConditionalFact]
    public Task UpsertCanBothInsertAndUpdateRecordsFromTheSameBatch_WithoutVectors()
        => this.UpsertCanBothInsertAndUpdateRecordsFromTheSameBatch(includeVectors: false);

    private async Task UpsertCanBothInsertAndUpdateRecordsFromTheSameBatch(bool includeVectors)
    {
        SimpleModel<TKey>[] records = Enumerable.Range(0, 10).Select(i => new SimpleModel<TKey>()
        {
            Id = fixture.GenerateNextKey<TKey>(),
            Number = 100 + i,
            Text = i.ToString(),
            Floats = Enumerable.Range(0, SimpleModel<TKey>.DimensionCount).Select(j => (float)(i + j)).ToArray()
        }).ToArray();

        // We take first half of the records and insert them.
        SimpleModel<TKey>[] firstHalf = records.Take(records.Length / 2).ToArray();
        TKey[] insertedKeys = await fixture.Collection.UpsertBatchAsync(firstHalf).ToArrayAsync();
        Assert.Equal(
            firstHalf.Select(r => r.Id).OrderBy(id => id).ToArray(),
            insertedKeys.OrderBy(id => id).ToArray());

        // Now we modify the first half of the records.
        foreach (var record in firstHalf)
        {
            record.Text += "updated";
            record.Number += 200;
        }

        // And now we upsert all the records (the first half is an update, the second is an insert).
        TKey[] mixedKeys = await fixture.Collection.UpsertBatchAsync(records).ToArrayAsync();
        Assert.Equal(
            records.Select(r => r.Id).OrderBy(id => id).ToArray(),
            mixedKeys.OrderBy(id => id).ToArray());

        var received = await fixture.Collection.GetBatchAsync(mixedKeys, new() { IncludeVectors = includeVectors }).ToArrayAsync();
        foreach (var record in records)
        {
            record.AssertEqual(this.GetRecord(received, record.Id), includeVectors);
        }
    }

    [ConditionalFact]
    public async Task DeleteBatchAsyncDoesNotThrowForEmptyBatch()
    {
        await fixture.Collection.DeleteBatchAsync([]);
    }

    [ConditionalFact]
    public async Task DeleteBatchAsyncThrowsArgumentNullExceptionForNullKeys()
    {
        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => fixture.Collection.DeleteBatchAsync(keys: null!));
        Assert.Equal("keys", ex.ParamName);
    }

    [ConditionalFact]
    public async Task DeleteBatchAsyncDeletesTheRecords()
    {
        TKey[] idsToRemove = [fixture.TestData[2].Id, fixture.TestData[3].Id];

        Assert.NotEmpty(await fixture.Collection.GetBatchAsync(idsToRemove).ToArrayAsync());
        await fixture.Collection.DeleteBatchAsync(idsToRemove);
        Assert.Empty(await fixture.Collection.GetBatchAsync(idsToRemove).ToArrayAsync());
    }

    // The order of records in the received array is not guaranteed
    // to match the order of keys in the requested keys array.
    protected SimpleModel<TKey> GetRecord(SimpleModel<TKey>[] received, TKey key)
        => received.Single(r => r.Id!.Equals(key));
}
