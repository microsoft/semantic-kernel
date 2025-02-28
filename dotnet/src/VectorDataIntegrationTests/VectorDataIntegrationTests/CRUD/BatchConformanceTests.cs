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
}
