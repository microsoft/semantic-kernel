// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

public class RecordConformanceTests<TKey>(VectorStoreFixture fixture)
    : ConformanceTestsBase<TKey, SimpleModel<TKey>>(fixture) where TKey : notnull
{
    [ConditionalFact]
    public async Task ReadingAndDeletingNonExistingRecordDoesNotThrow()
    {
        await this.ExecuteAsync(async collection =>
        {
            TKey key = this.Fixture.GenerateNextKey<TKey>();

            Assert.Null(await collection.GetAsync(key));
            await collection.DeleteAsync(key);
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
            TKey expectedKey = this.Fixture.GenerateNextKey<TKey>();
            SimpleModel<TKey> inserted = new()
            {
                Id = expectedKey,
                Text = "some",
                Number = 123,
                Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.1f, SimpleModel<TKey>.DimensionCount).ToArray())
            };

            TKey key = await collection.UpsertAsync(inserted);
            Assert.Equal(expectedKey, key);

            SimpleModel<TKey>? received = await collection.GetAsync(expectedKey, new() { IncludeVectors = includeVectors });
            this.AssertEqual(inserted, received, includeVectors);

            SimpleModel<TKey> updated = new()
            {
                Id = expectedKey,
                Text = "updated",
                Number = 456,
                Floats = new ReadOnlyMemory<float>(Enumerable.Repeat(0.2f, SimpleModel<TKey>.DimensionCount).ToArray())
            };

            key = await collection.UpsertAsync(updated);
            Assert.Equal(expectedKey, key);

            received = await collection.GetAsync(expectedKey, new() { IncludeVectors = includeVectors });
            this.AssertEqual(updated, received, includeVectors);

            await collection.DeleteAsync(key);

            received = await collection.GetAsync(key);
            Assert.Null(received);
        });
    }
}
