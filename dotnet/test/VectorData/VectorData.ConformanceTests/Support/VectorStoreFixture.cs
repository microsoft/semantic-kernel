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

    public virtual string GetUniqueCollectionName() => Guid.NewGuid().ToString();

    public virtual Task InitializeAsync()
        => this.TestStore.ReferenceCountingStartAsync();

    public virtual Task DisposeAsync()
        => this.TestStore.ReferenceCountingStopAsync();

    public virtual TKey GenerateNextKey<TKey>()
        => this.TestStore.GenerateKey<TKey>(Interlocked.Increment(ref this._nextKeyValue));
}
