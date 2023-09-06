// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;

namespace Microsoft.SemanticKernel.Connectors.Memory.USearch;

internal interface ICollectionLockStore
{
    object GetLockFor(string key);
    void RemoveLockFor(string key);
}

internal sealed class USearchConcurrentCollectionLockStore : ICollectionLockStore
{
    private readonly ConcurrentDictionary<string, object> _keyLockerMap;

    public USearchConcurrentCollectionLockStore() => this._keyLockerMap = new();

    public object GetLockFor(string key)
    {
        return this._keyLockerMap.GetOrAdd(key, k => new object());
    }

    public void RemoveLockFor(string key)
    {
        this._keyLockerMap.TryRemove(key, out _);
    }
}
