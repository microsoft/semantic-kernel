// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests.Models;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace VectorData.ConformanceTests.Collections;

public abstract class CollectionConformanceTests<TKey>(VectorStoreFixture fixture) : IAsyncLifetime
    where TKey : notnull
{
    public Task InitializeAsync()
        => fixture.VectorStore.EnsureCollectionDeletedAsync(this.CollectionName);

    [ConditionalFact]
    public async Task Collection_Ensure_Exists_Delete()
    {
        var collection = this.GetCollection();

        Assert.False(await collection.CollectionExistsAsync());
        await collection.EnsureCollectionExistsAsync();
        Assert.True(await collection.CollectionExistsAsync());
        await collection.EnsureCollectionDeletedAsync();
        Assert.False(await collection.CollectionExistsAsync());

        // Deleting a non-existing collection does not throw
        await fixture.TestStore.DefaultVectorStore.EnsureCollectionDeletedAsync(collection.Name);
    }

    [ConditionalFact]
    public async Task EnsureCollectionExists_twice_does_not_throw()
    {
        var collection = this.GetCollection();

        await collection.EnsureCollectionExistsAsync();
        await collection.EnsureCollectionExistsAsync();
        Assert.True(await collection.CollectionExistsAsync());
    }

    [ConditionalFact]
    public async Task Store_CollectionExists()
    {
        var store = fixture.VectorStore;
        var collection = this.GetCollection();

        Assert.False(await store.CollectionExistsAsync(collection.Name));
        await collection.EnsureCollectionExistsAsync();
        Assert.True(await store.CollectionExistsAsync(collection.Name));
    }

    [ConditionalFact]
    public async Task Store_DeleteCollection()
    {
        var store = fixture.VectorStore;
        var collection = this.GetCollection();

        await collection.EnsureCollectionExistsAsync();
        await fixture.TestStore.DefaultVectorStore.EnsureCollectionDeletedAsync(collection.Name);
        Assert.False(await collection.CollectionExistsAsync());
    }

    [ConditionalFact]
    public async Task Store_ListCollections()
    {
        var store = fixture.VectorStore;
        var collection = this.GetCollection();

        Assert.Empty(await store.ListCollectionNamesAsync().Where(n => n == collection.Name).ToListAsync());

        await collection.EnsureCollectionExistsAsync();

        var name = Assert.Single(await store.ListCollectionNamesAsync().Where(n => n == collection.Name).ToListAsync());
        Assert.Equal(collection.Name, name);
    }

    [ConditionalFact]
    public void Collection_metadata()
    {
        var collection = this.GetCollection();

        var collectionMetadata = (VectorStoreCollectionMetadata?)collection.GetService(typeof(VectorStoreCollectionMetadata));

        Assert.NotNull(collectionMetadata);
        Assert.NotNull(collectionMetadata.VectorStoreSystemName);
        Assert.NotNull(collectionMetadata.CollectionName);
    }

    public virtual string CollectionName => "CollectionTests";

    public virtual VectorStoreCollection<TKey, SimpleRecord<TKey>> GetCollection()
        => fixture.TestStore.DefaultVectorStore.GetCollection<TKey, SimpleRecord<TKey>>(this.CollectionName, this.CreateRecordDefinition());

    public virtual VectorStoreCollectionDefinition CreateRecordDefinition()
        => new()
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(SimpleRecord<object>.Id), typeof(TKey)) { StorageName = "key" },
                new VectorStoreDataProperty(nameof(SimpleRecord<object>.Text), typeof(string)) { StorageName = "text" },
                new VectorStoreDataProperty(nameof(SimpleRecord<object>.Number), typeof(int)) { StorageName = "number" },
                new VectorStoreVectorProperty(nameof(SimpleRecord<object>.Floats), typeof(ReadOnlyMemory<float>), 10) { IndexKind = fixture.TestStore.DefaultIndexKind }
            ]
        };

    public Task DisposeAsync() => Task.CompletedTask;
}
