// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace VectorDataSpecificationTests.Support;

public abstract class VectorStoreFixture : IAsyncLifetime
{
    private int _nextKeyValue = 1;

    public abstract TestStore TestStore { get; }

    public virtual string DefaultDistanceFunction => this.TestStore.DefaultDistanceFunction;
    public virtual string DefaultIndexKind => this.TestStore.DefaultIndexKind;

    public virtual Task InitializeAsync()
        => this.TestStore.ReferenceCountingStartAsync();

    public virtual Task DisposeAsync()
        => this.TestStore.ReferenceCountingStopAsync();

    public virtual TKey GenerateNextKey<TKey>()
        => this.TestStore.GenerateKey<TKey>(this._nextKeyValue++);
}
