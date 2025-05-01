// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace VectorDataSpecificationTests.Support;

#pragma warning disable CA1721 // Property names should not match get methods

/// <summary>
/// A test fixture that sets up a single collection in the test vector store, with a specific record definition
/// and test data.
/// </summary>
public abstract class VectorStoreCollectionFixture<TKey, TRecord> : VectorStoreFixture
    where TKey : notnull
    where TRecord : notnull
{
    private List<TRecord>? _testData;

    public abstract VectorStoreRecordDefinition GetRecordDefinition();
    protected abstract List<TRecord> BuildTestData();

    public virtual string CollectionName => Guid.NewGuid().ToString();
    protected virtual string DistanceFunction => this.TestStore.DefaultDistanceFunction;
    protected virtual string IndexKind => this.TestStore.DefaultIndexKind;

    protected virtual IVectorStoreRecordCollection<TKey, TRecord> GetCollection()
        => this.TestStore.DefaultVectorStore.GetCollection<TKey, TRecord>(this.CollectionName, this.GetRecordDefinition());

    public override async Task InitializeAsync()
    {
        await base.InitializeAsync();

        this.Collection = this.GetCollection();

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
        await this.Collection.UpsertAsync(this.TestData);
        await this.WaitForDataAsync();
    }

    protected virtual Task WaitForDataAsync()
        => this.TestStore.WaitForDataAsync(this.Collection, recordCount: this.TestData.Count);
}
