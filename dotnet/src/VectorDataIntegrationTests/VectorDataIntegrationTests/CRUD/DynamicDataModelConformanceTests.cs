// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

public abstract class DynamicDataModelConformanceTests<TKey>(DynamicDataModelFixture<TKey> fixture)
    where TKey : notnull
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

        var received = await fixture.Collection.GetAsync(
            (TKey)expectedRecord[DynamicDataModelFixture<TKey>.KeyPropertyName]!,
            new() { IncludeVectors = includeVectors });

        AssertEquivalent(expectedRecord, received, includeVectors, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task UpsertAsyncCanInsertNewRecord()
    {
        var collection = fixture.Collection;
        TKey expectedKey = fixture.GenerateNextKey<TKey>();
        var inserted = new Dictionary<string, object?>
        {
            [DynamicDataModelFixture<TKey>.KeyPropertyName] = expectedKey,
            [DynamicDataModelFixture<TKey>.StringPropertyName] = "some",
            [DynamicDataModelFixture<TKey>.IntegerPropertyName] = 123,
            [DynamicDataModelFixture<TKey>.EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.1f, DynamicDataModelFixture<TKey>.DimensionCount).ToArray())
        };

        Assert.Null(await collection.GetAsync(expectedKey));
        var key = await collection.UpsertAsync(inserted);
        Assert.Equal(expectedKey, key);

        var received = await collection.GetAsync(expectedKey, new() { IncludeVectors = true });
        AssertEquivalent(inserted, received, includeVectors: true, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task UpsertAsyncCanUpdateExistingRecord()
    {
        var collection = fixture.Collection;
        var existingRecord = fixture.TestData[1];
        var updated = new Dictionary<string, object?>
        {
            [DynamicDataModelFixture<TKey>.KeyPropertyName] = existingRecord[DynamicDataModelFixture<TKey>.KeyPropertyName],
            [DynamicDataModelFixture<TKey>.StringPropertyName] = "different",
            [DynamicDataModelFixture<TKey>.IntegerPropertyName] = 456,
            [DynamicDataModelFixture<TKey>.EmbeddingPropertyName] = new ReadOnlyMemory<float>(Enumerable.Repeat(0.7f, DynamicDataModelFixture<TKey>.DimensionCount).ToArray())
        };

        Assert.NotNull(await collection.GetAsync((TKey)existingRecord[DynamicDataModelFixture<TKey>.KeyPropertyName]!));
        var key = await collection.UpsertAsync(updated);
        Assert.Equal(existingRecord[DynamicDataModelFixture<TKey>.KeyPropertyName], key);

        var received = await collection.GetAsync((TKey)existingRecord[DynamicDataModelFixture<TKey>.KeyPropertyName]!, new() { IncludeVectors = true });
        AssertEquivalent(updated, received, includeVectors: true, fixture.TestStore.VectorsComparable);
    }

    [ConditionalFact]
    public virtual async Task DeleteAsyncDoesNotThrowForNonExistingKey()
    {
        TKey key = fixture.GenerateNextKey<TKey>();

        await fixture.Collection.DeleteAsync(key);
    }

    [ConditionalFact]
    public async Task DeleteAsyncDeletesTheRecord()
    {
        var recordToRemove = fixture.TestData[2];

        Assert.NotNull(await fixture.Collection.GetAsync((TKey)recordToRemove[DynamicDataModelFixture<TKey>.KeyPropertyName]!));
        await fixture.Collection.DeleteAsync((TKey)recordToRemove[DynamicDataModelFixture<TKey>.KeyPropertyName]!);
        Assert.Null(await fixture.Collection.GetAsync((TKey)recordToRemove[DynamicDataModelFixture<TKey>.KeyPropertyName]!));
    }

    protected static void AssertEquivalent(Dictionary<string, object?> expected, Dictionary<string, object?>? actual, bool includeVectors, bool compareVectors)
    {
        Assert.NotNull(actual);
        Assert.Equal(expected[DynamicDataModelFixture<TKey>.KeyPropertyName], actual[DynamicDataModelFixture<TKey>.KeyPropertyName]);

        Assert.Equal(expected[DynamicDataModelFixture<TKey>.StringPropertyName], actual[DynamicDataModelFixture<TKey>.StringPropertyName]);
        Assert.Equal(expected[DynamicDataModelFixture<TKey>.IntegerPropertyName], actual[DynamicDataModelFixture<TKey>.IntegerPropertyName]);

        if (includeVectors)
        {
            Assert.Equal(
                ((ReadOnlyMemory<float>)expected[DynamicDataModelFixture<TKey>.EmbeddingPropertyName]!).Length,
                ((ReadOnlyMemory<float>)actual[DynamicDataModelFixture<TKey>.EmbeddingPropertyName]!).Length);

            if (compareVectors)
            {
                Assert.Equal(
                    ((ReadOnlyMemory<float>)expected[DynamicDataModelFixture<TKey>.EmbeddingPropertyName]!).ToArray(),
                    ((ReadOnlyMemory<float>)actual[DynamicDataModelFixture<TKey>.EmbeddingPropertyName]!).ToArray());
            }
        }
        else
        {
            Assert.False(actual.ContainsKey(DynamicDataModelFixture<TKey>.EmbeddingPropertyName));
        }
    }
}
