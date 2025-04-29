// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

public class RecordConformanceTests<TKey>(SimpleModelFixture<TKey> fixture) where TKey : notnull
{
    [ConditionalFact]
    public virtual async Task GetAsyncThrowsArgumentNullExceptionForNullKey()
    {
        // Skip this test for value type keys
        if (default(TKey) is not null)
        {
            return;
        }

        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => fixture.Collection.GetAsync((TKey)default!));
        Assert.Equal("key", ex.ParamName);
    }

    [ConditionalFact]
    public virtual async Task GetAsyncReturnsNullForNonExistingKey()
    {
        TKey key = fixture.GenerateNextKey<TKey>();

        Assert.Null(await fixture.Collection.GetAsync(key));
    }

    [ConditionalFact]
    public virtual Task GetAsync_WithVectors()
        => this.GetAsyncReturnsInsertedRecord(includeVectors: true);

    [ConditionalFact]
    public virtual Task GetAsync_WithoutVectors()
        => this.GetAsyncReturnsInsertedRecord(includeVectors: false);

    private async Task GetAsyncReturnsInsertedRecord(bool includeVectors)
    {
        var expectedRecord = fixture.TestData[0];

        var received = await fixture.Collection.GetAsync(expectedRecord.Id, new() { IncludeVectors = includeVectors });

        expectedRecord.AssertEqual(received, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task UpsertAsyncCanInsertNewRecord()
    {
        var collection = fixture.Collection;
        TKey expectedKey = fixture.GenerateNextKey<TKey>();
        SimpleRecord<TKey> inserted = new()
        {
            Id = expectedKey,
            Text = "some",
            Number = 123,
            Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.1f, SimpleRecord<TKey>.DimensionCount).ToArray())
        };

        Assert.Null(await collection.GetAsync(expectedKey));
        TKey key = await collection.UpsertAsync(inserted);
        Assert.Equal(expectedKey, key);

        var received = await collection.GetAsync(expectedKey, new() { IncludeVectors = true });
        inserted.AssertEqual(received, includeVectors: true, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task UpsertAsyncCanUpdateExistingRecord()
    {
        var collection = fixture.Collection;
        var existingRecord = fixture.TestData[1];
        SimpleRecord<TKey> updated = new()
        {
            Id = existingRecord.Id,
            Text = "updated",
            Number = 456,
            Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.25f, SimpleRecord<TKey>.DimensionCount).ToArray())
        };

        Assert.NotNull(await collection.GetAsync(existingRecord.Id));
        TKey key = await collection.UpsertAsync(updated);
        Assert.Equal(existingRecord.Id, key);

        var received = await collection.GetAsync(existingRecord.Id, new() { IncludeVectors = true });
        updated.AssertEqual(received, includeVectors: true, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task DeleteAsyncDoesNotThrowForNonExistingKey()
    {
        TKey key = fixture.GenerateNextKey<TKey>();

        await fixture.Collection.DeleteAsync(key);
    }

    [ConditionalFact]
    public virtual async Task DeleteAsyncDeletesTheRecord()
    {
        var recordToRemove = fixture.TestData[2];

        Assert.NotNull(await fixture.Collection.GetAsync(recordToRemove.Id));
        await fixture.Collection.DeleteAsync(recordToRemove.Id);
        Assert.Null(await fixture.Collection.GetAsync(recordToRemove.Id));
    }
}
