// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Memory.Storage;

/// <summary>
/// An interface for storing and retrieving <see cref="IDataStore{TValue}"/> objects.
/// </summary>
/// <typeparam name="TValue">The type of data to be stored in this store.</typeparam>
public interface IDataStore<TValue>
{
    /// <summary>
    /// Gets a group of all available collection names.
    /// </summary>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>A group of collection names.</returns>
    IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default);

    /// <summary>
    /// Gets all entries within a collection.
    /// </summary>
    /// <param name="collection">Collection name.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>A collection of data; empty if collection doesn't exist.</returns>
    IAsyncEnumerable<DataEntry<TValue>> GetAllAsync(string collection, CancellationToken cancel = default);

    /// <summary>
    /// Gets a <see cref="IDataStore{TValue}"/> object given the data entry's collection and unique ID.
    /// </summary>
    /// <param name="collection">Collection name.</param>
    /// <param name="key">Unique Item key.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>The data, if found. Null otherwise.</returns>
    Task<DataEntry<TValue>?> GetAsync(string collection, string key, CancellationToken cancel = default);

    /// <summary>
    /// Updates or Inserts a data entry (Upsert).
    /// </summary>
    /// <param name="collection">Collection name.</param>
    /// <param name="data">The <see cref="DataEntry{TValue}"/> object to insert into the data store.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>Returns the unique key for the database entry</returns>
    Task<string> PutAsync(string collection, DataEntry<TValue> data, CancellationToken cancel = default);

    /// <summary>
    /// Removes a data entry from the store given the data entry's unique ID.
    /// </summary>
    /// <param name="collection">Collection name.</param>
    /// <param name="key">Unique Item key.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    Task RemoveAsync(string collection, string key, CancellationToken cancel = default);
};

/// <summary>
/// Common extension methods for <see cref="IDataStore{TValue}"/> objects.
/// </summary>
public static class DataStoreExtensions
{
    /// <summary>
    /// Gets the data value from a collection and key.
    /// </summary>
    /// <typeparam name="TValue">The data value type.</typeparam>
    /// <param name="store">The data store.</param>
    /// <param name="collection">The collection within the data store.</param>
    /// <param name="key">The unique key for the data within the collection.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>The data value, if found. Null otherwise.</returns>
    public static async Task<TValue?> GetValueAsync<TValue>(this IDataStore<TValue> store, string collection, string key, CancellationToken cancel = default)
    {
        Verify.NotNull(store, "Data store cannot be NULL");

        DataEntry<TValue>? dataEntry = await store.GetAsync(collection, key, cancel);
        if (dataEntry != null)
        {
            return (dataEntry.Value).Value;
        }

        return default;
    }

    /// <summary>
    /// Inserts a data entry. Updates if key is already present.
    /// </summary>
    /// <typeparam name="TValue">The data value type.</typeparam>
    /// <param name="store">The data store.</param>
    /// <param name="collection">The collection within the data store.</param>
    /// <param name="value">The data value.</param>
    /// <param name="dbKey">The unique database key.</param>
    /// <param name="timeStamp">The data timestamp.</param>
    /// <param name="cancel">Cancellation token.</param>
    public static Task<string> PutValueAsync<TValue>(
        this IDataStore<TValue> store,
        string collection,
        TValue? value,
        string? dbKey = null,
        DateTimeOffset? timeStamp = null,
        CancellationToken cancel = default)
    {
        Verify.NotNull(store, "Data store cannot be NULL");

        DataEntry<TValue> entry = DataEntry.Create(dbKey, value, timeStamp);
        return store.PutAsync(collection, entry, cancel);
    }
}
