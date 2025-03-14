// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

public class RecordConformanceTests<TKey>(SimpleModelFixture<TKey> fixture) where TKey : notnull
{
    [ConditionalFact]
    public async Task GetAsyncThrowsArgumentNullExceptionForNullKey()
    {
        ArgumentNullException ex = await Assert.ThrowsAsync<ArgumentNullException>(() => fixture.Collection.GetAsync(default!));
        Assert.Equal("key", ex.ParamName);
    }

    [ConditionalFact]
    public async Task GetAsyncReturnsNullForNonExistingKey()
    {
        TKey key = fixture.GenerateNextKey<TKey>();

        Assert.Null(await fixture.Collection.GetAsync(key));
    }

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

        expectedRecord.AssertEqual(received, includeVectors);
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
        SimpleModel<TKey> inserted = new()
        {
            Id = expectedKey,
            Text = "some",
            Number = 123,
            Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.1f, SimpleModel<TKey>.DimensionCount).ToArray())
        };

        Assert.Null(await collection.GetAsync(expectedKey));
        TKey key = await collection.UpsertAsync(inserted);
        Assert.Equal(expectedKey, key);

        var received = await collection.GetAsync(expectedKey, new() { IncludeVectors = includeVectors });
        inserted.AssertEqual(received, includeVectors);
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
        SimpleModel<TKey> updated = new()
        {
            Id = existingRecord.Id,
            Text = "updated",
            Number = 456,
            Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.2f, SimpleModel<TKey>.DimensionCount).ToArray())
        };

        Assert.NotNull(await collection.GetAsync(existingRecord.Id));
        TKey key = await collection.UpsertAsync(updated);
        Assert.Equal(existingRecord.Id, key);

        var received = await collection.GetAsync(existingRecord.Id, new() { IncludeVectors = includeVectors });
        updated.AssertEqual(received, includeVectors);
    }

    [ConditionalFact]
    public async Task DeleteAsyncDoesNotThrowForNonExistingKey()
    {
        TKey key = fixture.GenerateNextKey<TKey>();

        await fixture.Collection.DeleteAsync(key);
    }

    [ConditionalFact]
    public async Task DeleteAsyncDeletesTheRecord()
    {
        var recordToRemove = fixture.TestData[2];

        Assert.NotNull(await fixture.Collection.GetAsync(recordToRemove.Id));
        await fixture.Collection.DeleteAsync(recordToRemove.Id);
        Assert.Null(await fixture.Collection.GetAsync(recordToRemove.Id));
    }
}
