// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Xunit;

namespace VectorData.ConformanceTests.Support;

public abstract class VectorStoreFixture : IAsyncLifetime
{
    private int _nextKeyValue = 1;

    public abstract TestStore TestStore { get; }
    public virtual VectorStore VectorStore => this.TestStore.DefaultVectorStore;

    public virtual string DefaultDistanceFunction => this.TestStore.DefaultDistanceFunction;
    public virtual string DefaultIndexKind => this.TestStore.DefaultIndexKind;

    public virtual Task InitializeAsync()
        => this.TestStore.ReferenceCountingStartAsync();

    public virtual Task DisposeAsync()
        => this.TestStore.ReferenceCountingStopAsync();

    public virtual TKey GenerateNextKey<TKey>()
        => this.TestStore.GenerateKey<TKey>(Interlocked.Increment(ref this._nextKeyValue));

    /// <summary>
    /// Creates a collection for the given name and definition.
    /// Delegates to <see cref="TestStore.CreateCollection{TKey, TRecord}"/> which can be overridden for provider-specific options.
    /// </summary>
    public virtual VectorStoreCollection<TKey, TRecord> CreateCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition definition)
        where TKey : notnull
        where TRecord : class
        => this.TestStore.CreateCollection<TKey, TRecord>(name, definition);

    /// <summary>
    /// Creates a dynamic collection for the given name and definition.
    /// Delegates to <see cref="TestStore.CreateDynamicCollection"/> which can be overridden for provider-specific options.
    /// </summary>
    public virtual VectorStoreCollection<object, Dictionary<string, object?>> CreateDynamicCollection(string name, VectorStoreCollectionDefinition definition)
        => this.TestStore.CreateDynamicCollection(name, definition);
}
