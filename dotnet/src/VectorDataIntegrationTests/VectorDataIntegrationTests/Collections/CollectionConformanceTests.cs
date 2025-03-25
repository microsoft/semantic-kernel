// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Models;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace VectorDataSpecificationTests.Collections;

public abstract class CollectionConformanceTests<TKey>(VectorStoreFixture fixture) where TKey : notnull
{
    [ConditionalFact]
    public Task DeleteCollectionDoesNotThrowForNonExistingCollection()
         => this.DeleteNonExistingCollection<SimpleModel<TKey>>();

    [ConditionalFact]
    public Task DeleteCollectionDoesNotThrowForNonExistingCollection_GenericDataModel()
        => this.DeleteNonExistingCollection<VectorStoreGenericDataModel<TKey>>();

    [ConditionalFact]
    public Task CreateCollectionCreatesTheCollection()
        => this.CreateCollection<SimpleModel<TKey>>();

    [ConditionalFact]
    public Task CreateCollectionCreatesTheCollection_GenericDataModel()
        => this.CreateCollection<VectorStoreGenericDataModel<TKey>>();

    [ConditionalFact]
    public Task CreateCollectionIfNotExistsCalledMoreThanOnceDoesNotThrow()
        => this.CreateCollectionIfNotExistsMoreThanOnce<SimpleModel<TKey>>();

    [ConditionalFact]
    public Task CreateCollectionIfNotExistsCalledMoreThanOnceDoesNotThrow_GenericDataModel()
        => this.CreateCollectionIfNotExistsMoreThanOnce<VectorStoreGenericDataModel<TKey>>();

    [ConditionalFact]
    public Task CreateCollectionCalledMoreThanOnceThrowsVectorStoreOperationException()
        => this.CreateCollectionMoreThanOnce<SimpleModel<TKey>>();

    [ConditionalFact]
    public Task CreateCollectionCalledMoreThanOnceThrowsVectorStoreOperationException_GenericDataModel()
        => this.CreateCollectionMoreThanOnce<VectorStoreGenericDataModel<TKey>>();

    private async Task<IVectorStoreRecordCollection<TKey, TRecord>> GetNonExistingCollectionAsync<TRecord>()
    {
        var collectionName = fixture.GetUniqueCollectionName();
        VectorStoreRecordDefinition? definition = null;
        if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<TKey>))
        {
            definition = new()
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty(nameof(VectorStoreGenericDataModel<TKey>.Key), typeof(TKey)),
                    new VectorStoreRecordDataProperty("string", typeof(string)),
                    new VectorStoreRecordDataProperty("integer", typeof(int)),
                    new VectorStoreRecordVectorProperty("embedding", typeof(ReadOnlyMemory<float>))
                    {
                        Dimensions = 10
                    }
                ]
            };
        }

        var collection = fixture.TestStore.DefaultVectorStore.GetCollection<TKey, TRecord>(collectionName, definition);

        Assert.False(await collection.CollectionExistsAsync());

        return collection;
    }

    private async Task DeleteNonExistingCollection<TRecord>()
    {
        var collection = await this.GetNonExistingCollectionAsync<TRecord>();

        await collection.DeleteCollectionAsync();
    }

    private async Task CreateCollection<TRecord>()
    {
        var collection = await this.GetNonExistingCollectionAsync<TRecord>();

        await collection.CreateCollectionAsync();

        try
        {
            Assert.True(await collection.CollectionExistsAsync());
            Assert.True(await fixture.TestStore.DefaultVectorStore.ListCollectionNamesAsync().ContainsAsync(collection.CollectionName));
        }
        finally
        {
            await collection.DeleteCollectionAsync();
        }
    }

    private async Task CreateCollectionIfNotExistsMoreThanOnce<TRecord>()
    {
        var collection = await this.GetNonExistingCollectionAsync<TRecord>();

        await collection.CreateCollectionIfNotExistsAsync();

        try
        {
            Assert.True(await collection.CollectionExistsAsync());
            Assert.True(await fixture.TestStore.DefaultVectorStore.ListCollectionNamesAsync().ContainsAsync(collection.CollectionName));

            await collection.CreateCollectionIfNotExistsAsync();
        }
        finally
        {
            await collection.DeleteCollectionAsync();
        }
    }

    private async Task CreateCollectionMoreThanOnce<TRecord>()
    {
        var collection = await this.GetNonExistingCollectionAsync<TRecord>();

        await collection.CreateCollectionAsync();

        try
        {
            Assert.True(await collection.CollectionExistsAsync());
            Assert.True(await fixture.TestStore.DefaultVectorStore.ListCollectionNamesAsync().ContainsAsync(collection.CollectionName));

            await collection.CreateCollectionIfNotExistsAsync();

            await Assert.ThrowsAsync<VectorStoreOperationException>(() => collection.CreateCollectionAsync());
        }
        finally
        {
            await collection.DeleteCollectionAsync();
        }
    }
}
