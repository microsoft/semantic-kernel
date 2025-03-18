// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

public abstract class GenericDataModelConformanceTests<TKey>(GenericDataModelFixture<TKey> fixture) where TKey : notnull
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

        var received = await fixture.Collection.GetAsync(expectedRecord.Key, new() { IncludeVectors = includeVectors });

        AssertEqual(expectedRecord, received, includeVectors);
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
        VectorStoreGenericDataModel<TKey> inserted = new(expectedKey)
        {
            Data =
            {
                [GenericDataModelFixture<TKey>.StringPropertyName] = "some",
                [GenericDataModelFixture<TKey>.IntegerPropertyName] = 123
            },
            Vectors =
            {
                [GenericDataModelFixture<TKey>.EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.1f, GenericDataModelFixture<TKey>.DimensionCount).ToArray())
            }
        };

        Assert.Null(await collection.GetAsync(expectedKey));
        TKey key = await collection.UpsertAsync(inserted);
        Assert.Equal(expectedKey, key);

        var received = await collection.GetAsync(expectedKey, new() { IncludeVectors = includeVectors });
        AssertEqual(inserted, received, includeVectors);
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
        VectorStoreGenericDataModel<TKey> updated = new(existingRecord.Key)
        {
            Data =
            {
                [GenericDataModelFixture<TKey>.StringPropertyName] = "different",
                [GenericDataModelFixture<TKey>.IntegerPropertyName] = 456
            },
            Vectors =
            {
                [GenericDataModelFixture<TKey>.EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.7f, GenericDataModelFixture<TKey>.DimensionCount).ToArray())
            }
        };

        Assert.NotNull(await collection.GetAsync(existingRecord.Key));
        TKey key = await collection.UpsertAsync(updated);
        Assert.Equal(existingRecord.Key, key);

        var received = await collection.GetAsync(existingRecord.Key, new() { IncludeVectors = includeVectors });
        AssertEqual(updated, received, includeVectors);
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

        Assert.NotNull(await fixture.Collection.GetAsync(recordToRemove.Key));
        await fixture.Collection.DeleteAsync(recordToRemove.Key);
        Assert.Null(await fixture.Collection.GetAsync(recordToRemove.Key));
    }

    private static void AssertEqual(VectorStoreGenericDataModel<TKey> expected, VectorStoreGenericDataModel<TKey>? actual, bool includeVectors)
    {
        Assert.NotNull(actual);
        Assert.Equal(expected.Key, actual.Key);
        foreach (var pair in expected.Data)
        {
            Assert.Equal(pair.Value, actual.Data[pair.Key]);
        }

        if (includeVectors)
        {
            Assert.Equal(
                ((ReadOnlyMemory<float>)expected.Vectors[GenericDataModelFixture<TKey>.EmbeddingPropertyName]!).ToArray(),
                ((ReadOnlyMemory<float>)actual.Vectors[GenericDataModelFixture<TKey>.EmbeddingPropertyName]!).ToArray());
        }
        else
        {
            Assert.Empty(actual.Vectors);
        }
    }
}
