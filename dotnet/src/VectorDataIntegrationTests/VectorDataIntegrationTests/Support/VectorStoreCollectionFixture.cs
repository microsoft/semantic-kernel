// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace VectorDataSpecificationTests.Support;

/// <summary>
/// A test fixture that sets up a single collection in the test vector store, with a specific record definition
/// and test data.
/// </summary>
public abstract class VectorStoreCollectionFixture<TKey, TRecord> : VectorStoreFixture
    where TKey : notnull
{
    private List<TRecord>? _testData;

    protected abstract VectorStoreRecordDefinition GetRecordDefinition();
    protected abstract List<TRecord> BuildTestData();

    protected virtual string CollectionName => Guid.NewGuid().ToString();
    protected virtual string DistanceFunction => this.TestStore.DefaultDistanceFunction;
    protected virtual string IndexKind => this.TestStore.DefaultIndexKind;

    protected virtual IVectorStoreRecordCollection<TKey, TRecord> CreateCollection()
        => this.TestStore.DefaultVectorStore.GetCollection<TKey, TRecord>(this.CollectionName, this.GetRecordDefinition());

    public override async Task InitializeAsync()
    {
        await base.InitializeAsync();

        this.Collection = this.CreateCollection();

        if (await this.Collection.CollectionExistsAsync())
        {
            await this.Collection.DeleteCollectionAsync();
        }

        await this.Collection.CreateCollectionAsync();
        await this.SeedAsync();
    }

    public virtual IVectorStoreRecordCollection<TKey, TRecord> Collection { get; private set; } = null!;

    public List<TRecord> TestData => this._testData ??= this.BuildTestData();

    protected virtual async Task SeedAsync()
    {
        // TODO: UpsertBatchAsync returns IAsyncEnumerable<TKey> (to support server-generated keys?), but this makes it quite hard to use:
        await foreach (var _ in this.Collection.UpsertBatchAsync(this.TestData))
        {
        }

        await this.WaitForDataAsync();
    }

    protected virtual Task WaitForDataAsync()
        => this.TestStore.WaitForDataAsync(this.Collection, recordCount: this.TestData.Count);
}
