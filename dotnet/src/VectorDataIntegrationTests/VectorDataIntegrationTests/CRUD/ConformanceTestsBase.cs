// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using VectorDataSpecificationTests.Support;

namespace VectorDataSpecificationTests.CRUD;

// TKey is a generic parameter because different connectors support different key types.
public abstract class ConformanceTestsBase<TKey, TRecord>(VectorStoreFixture fixture) where TKey : notnull
{
    protected VectorStoreFixture Fixture { get; } = fixture;

    protected virtual string GetUniqueCollectionName() => Guid.NewGuid().ToString();

    protected virtual VectorStoreRecordDefinition? GetRecordDefinition() => null;

    protected async Task ExecuteAsync(Func<IVectorStoreRecordCollection<TKey, TRecord>, Task> test)
    {
        string collectionName = this.GetUniqueCollectionName();
        var collection = this.Fixture.TestStore.DefaultVectorStore.GetCollection<TKey, TRecord>(collectionName,
            this.GetRecordDefinition());

        await collection.CreateCollectionAsync();

        try
        {
            await test(collection);
        }
        finally
        {
            await collection.DeleteCollectionAsync();
        }
    }
}
