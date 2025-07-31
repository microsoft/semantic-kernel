// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that provides a channel interacting with custom storage
/// </summary>
public interface IProcessStorageConnector
{
    /// <summary>
    /// Logic executed when creating a new storage connection
    /// </summary>
    /// <returns>A <see cref="ValueTask"/></returns>
    abstract ValueTask OpenConnectionAsync();

    /// <summary>
    /// Logic executed when closing opened storage connection
    /// </summary>
    /// <returns>A <see cref="ValueTask"/></returns>
    abstract ValueTask CloseConnectionAsync();

    /// <summary>
    /// Get specific entry type by id
    /// </summary>
    /// <typeparam name="TEntry">class that defines the entry type to be extracted from storage</typeparam>
    /// <param name="id">id of entry used storage</param>
    /// <returns></returns>
    abstract Task<TEntry?> GetEntryAsync<TEntry>(string id) where TEntry : class;

    /// <summary>
    /// Save specific entry type with assigned id
    /// </summary>
    /// <typeparam name="TEntry"></typeparam>
    /// <param name="id">id of entry used storage</param>
    /// <param name="type">type of entry used in storage</param>
    /// <param name="entry">data to be stored in storage</param>
    /// <returns></returns>
    abstract Task<bool> SaveEntryAsync<TEntry>(string id, string type, TEntry entry) where TEntry : class;

    /// <summary>
    /// Delete specific entry from storage
    /// </summary>
    /// <param name="id">id of entry used storage</param>
    /// <returns></returns>
    abstract Task<bool> DeleteEntryAsync(string id);
}
