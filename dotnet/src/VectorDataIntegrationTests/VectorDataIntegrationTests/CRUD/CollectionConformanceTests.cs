// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.CRUD;

public class CollectionConformanceTests<TKey>(VectorStoreFixture fixture)
    : ConformanceTestsBase<TKey, SimpleModel<TKey>>(fixture) where TKey : notnull
{
    [ConditionalFact]
    public async Task DeletingNonExistingCollectionDoesNotThrow()
    {
        await this.ExecuteAsync(async collection =>
        {
            Assert.False(await collection.CollectionExistsAsync());

            await collection.DeleteCollectionAsync();
        }, createCollection: false);
    }

    [ConditionalFact]
    public async Task CreateCollectionIfNotExistsCalledMoreThanOnceDoesNotThrow()
    {
        await this.ExecuteAsync(async collection =>
        {
            Assert.False(await collection.CollectionExistsAsync());

            await collection.CreateCollectionIfNotExistsAsync();
            Assert.True(await collection.CollectionExistsAsync());
            Assert.True(await this.Fixture.TestStore.DefaultVectorStore.ListCollectionNamesAsync().ContainsAsync(collection.CollectionName));

            await collection.CreateCollectionIfNotExistsAsync();
        }, createCollection: false);
    }

    [ConditionalFact]
    public async Task CreateCollectionAsyncCalledMoreThanOnceThrows()
    {
        await this.ExecuteAsync(async collection =>
        {
            Assert.False(await collection.CollectionExistsAsync());

            await collection.CreateCollectionAsync();
            Assert.True(await collection.CollectionExistsAsync());
            Assert.True(await this.Fixture.TestStore.DefaultVectorStore.ListCollectionNamesAsync().ContainsAsync(collection.CollectionName));

            await collection.CreateCollectionIfNotExistsAsync();

            await Assert.ThrowsAsync<VectorStoreOperationException>(() => collection.CreateCollectionAsync());
        }, createCollection: false);
    }
}
