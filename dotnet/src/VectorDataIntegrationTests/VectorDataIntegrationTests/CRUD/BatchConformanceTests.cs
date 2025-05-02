// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

public abstract class BatchConformanceTests<TKey>(SimpleModelFixture<TKey> fixture) where TKey : notnull
{
    [ConditionalFact]
    public virtual async Task GetBatchAsyncThrowsArgumentNullExceptionForNullKeys()
    {
        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => fixture.Collection.GetAsync(keys: null!).ToArrayAsync().AsTask());
        Assert.Equal("keys", ex.ParamName);
    }

    [ConditionalFact]
    public virtual async Task GetBatchAsyncDoesNotThrowForEmptyBatch()
    {
        Assert.Empty(await fixture.Collection.GetAsync([]).ToArrayAsync());
    }

    [ConditionalFact]
    public virtual Task GetBatchAsync_WithVectors()
        => this.GetBatchAsyncReturnsInsertedRecords(includeVectors: true);

    [ConditionalFact]
    public virtual Task GetBatchAsync_WithoutVectors()
        => this.GetBatchAsyncReturnsInsertedRecords(includeVectors: false);

    private async Task GetBatchAsyncReturnsInsertedRecords(bool includeVectors)
    {
        var expectedRecords = fixture.TestData.Take(2); // the last two records can get deleted by other tests
        var ids = expectedRecords.Select(record => record.Id);

        var received = await fixture.Collection.GetAsync(ids, new() { IncludeVectors = includeVectors }).ToArrayAsync();

        foreach (var record in expectedRecords)
        {
            record.AssertEqual(this.GetRecord(received, record.Id), includeVectors, fixture.TestStore.VectorsComparable);
        }
    }

    [ConditionalFact]
    public virtual async Task UpsertBatchAsyncThrowsArgumentNullExceptionForNullBatch()
    {
        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => fixture.Collection.UpsertAsync(records: null!));
        Assert.Equal("records", ex.ParamName);
    }

    [ConditionalFact]
    public virtual async Task UpsertBatchAsyncDoesNotThrowForEmptyBatch()
    {
        Assert.Empty(await fixture.Collection.UpsertAsync([]));
    }

    [ConditionalFact]
    public virtual async Task UpsertBatchAsyncCanInsertNewRecord()
    {
        var collection = fixture.Collection;
        SimpleRecord<TKey>[] inserted = Enumerable.Range(0, 10).Select(i => new SimpleRecord<TKey>()
        {
            Id = fixture.GenerateNextKey<TKey>(),
            Number = 100 + i,
            Text = i.ToString(),
            Floats = Enumerable.Range(0, SimpleRecord<TKey>.DimensionCount).Select(j => (float)(i + j)).ToArray()
        }).ToArray();
        var keys = inserted.Select(record => record.Id).ToArray();

        Assert.Empty(await collection.GetAsync(keys).ToArrayAsync());
        var receivedKeys = await collection.UpsertAsync(inserted);
        Assert.Equal(keys.ToHashSet(), receivedKeys.ToHashSet()); // .ToHashSet() to ignore order

        var received = await collection.GetAsync(keys, new() { IncludeVectors = true }).ToArrayAsync();
        foreach (var record in inserted)
        {
            record.AssertEqual(this.GetRecord(received, record.Id), includeVectors: true, fixture.TestStore.VectorsComparable);
        }
    }

    [ConditionalFact]
    public virtual async Task UpsertBatchAsyncCanUpdateExistingRecords()
    {
        SimpleRecord<TKey>[] inserted = Enumerable.Range(0, 10).Select(i => new SimpleRecord<TKey>()
        {
            Id = fixture.GenerateNextKey<TKey>(),
            Number = 100 + i,
            Text = i.ToString(),
            Floats = Enumerable.Range(0, SimpleRecord<TKey>.DimensionCount).Select(j => (float)(i + j)).ToArray()
        }).ToArray();
        await fixture.Collection.UpsertAsync(inserted);

        SimpleRecord<TKey>[] updated = inserted.Select(i => new SimpleRecord<TKey>()
        {
            Id = i.Id,
            Text = i.Text + "updated",
            Number = i.Number + 200,
            Floats = i.Floats
        }).ToArray();

        var keys = await fixture.Collection.UpsertAsync(updated);
        Assert.Equal(
            updated.Select(r => r.Id).OrderBy(id => id).ToArray(),
            keys.OrderBy(id => id).ToArray());

        var received = await fixture.Collection.GetAsync(keys, new() { IncludeVectors = true }).ToArrayAsync();
        foreach (var record in updated)
        {
            record.AssertEqual(this.GetRecord(received, record.Id), includeVectors: true, fixture.TestStore.VectorsComparable);
        }
    }

    [ConditionalFact]
    public virtual async Task UpsertCanBothInsertAndUpdateRecordsFromTheSameBatch()
    {
        SimpleRecord<TKey>[] records = Enumerable.Range(0, 10).Select(i => new SimpleRecord<TKey>()
        {
            Id = fixture.GenerateNextKey<TKey>(),
            Number = 100 + i,
            Text = i.ToString(),
            Floats = Enumerable.Range(0, SimpleRecord<TKey>.DimensionCount).Select(j => (float)(i + j)).ToArray()
        }).ToArray();

        // We take first half of the records and insert them.
        SimpleRecord<TKey>[] firstHalf = records.Take(records.Length / 2).ToArray();
        var insertedKeys = await fixture.Collection.UpsertAsync(firstHalf);
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
        var mixedKeys = await fixture.Collection.UpsertAsync(records);
        Assert.Equal(
            records.Select(r => r.Id).OrderBy(id => id).ToArray(),
            mixedKeys.OrderBy(id => id).ToArray());

        var received = await fixture.Collection.GetAsync(mixedKeys, new() { IncludeVectors = true }).ToArrayAsync();
        foreach (var record in records)
        {
            record.AssertEqual(this.GetRecord(received, record.Id), includeVectors: true, fixture.TestStore.VectorsComparable);
        }
    }

    [ConditionalFact]
    public virtual async Task DeleteBatchAsyncDoesNotThrowForEmptyBatch()
    {
        await fixture.Collection.DeleteAsync([]);
    }

    [ConditionalFact]
    public virtual async Task DeleteBatchAsyncThrowsArgumentNullExceptionForNullKeys()
    {
        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => fixture.Collection.DeleteAsync(keys: null!));
        Assert.Equal("keys", ex.ParamName);
    }

    [ConditionalFact]
    public virtual async Task DeleteBatchAsyncDeletesTheRecords()
    {
        TKey[] idsToRemove = [fixture.TestData[2].Id, fixture.TestData[3].Id];

        Assert.NotEmpty(await fixture.Collection.GetAsync(idsToRemove).ToArrayAsync());
        await fixture.Collection.DeleteAsync(idsToRemove);
        Assert.Empty(await fixture.Collection.GetAsync(idsToRemove).ToArrayAsync());
    }

    // The order of records in the received array is not guaranteed
    // to match the order of keys in the requested keys array.
    protected SimpleRecord<TKey> GetRecord(SimpleRecord<TKey>[] received, TKey key)
        => received.Single(r => r.Id!.Equals(key));
}
