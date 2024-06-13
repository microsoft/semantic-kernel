// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// An interface for adding, updating, deleting and retrieving records from a memory store.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <typeparam name="TDataModel">The data model to use for adding, updating and retrieving data from storage.</typeparam>
[Experimental("SKEXP0001")]
public interface IMemoryRecordService<TKey, TDataModel>
    where TDataModel : class
{
    /// <summary>
    /// Gets a memory record from the data store. Does not guarantee that the collection exists.
    /// Throws if the record is not found.
    /// </summary>
    /// <param name="key">The unique id associated with the memory record to get.</param>
    /// <param name="options">Optional options for retrieving the record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The memory record if found, otherwise null.</returns>
    /// <exception cref="MemoryServiceCommandExecutionException">Throw when the command fails to execute for any reason.</exception>
    /// <exception cref="MemoryDataModelMappingException">Throw when mapping between the storage model and data model fails.</exception>
    Task<TDataModel> GetAsync(TKey key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a batch of memory records from the data store. Does not guarantee that the collection exists.
    /// Throws if any of the records are not found.
    /// Gets will be made in a single request or in a single parallel batch depending on the available store functionality.
    /// </summary>
    /// <param name="keys">The unique ids associated with the memory record to get.</param>
    /// <param name="options">Optional options for retrieving the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The vecmemorytor records associated with the unique keys provided.</returns>
    /// <exception cref="MemoryServiceCommandExecutionException">Throw when the command fails to execute for any reason.</exception>
    /// <exception cref="MemoryDataModelMappingException">Throw when mapping between the storage model and data model fails.</exception>
    IAsyncEnumerable<TDataModel> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a memory record from the data store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="key">The unique id associated with the memory record to remove.</param>
    /// <param name="options">Optional options for removing the record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifier for the memory record.</returns>
    /// <exception cref="MemoryServiceCommandExecutionException">Throw when the command fails to execute for any reason.</exception>
    Task DeleteAsync(TKey key, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a batch of memory records from the data store. Does not guarantee that the collection exists.
    /// Deletes will be made in a single request or in a single parallel batch depending on the available store functionality.
    /// </summary>
    /// <param name="keys">The unique ids associated with the memory records to remove.</param>
    /// <param name="options">Optional options for removing the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <exception cref="MemoryServiceCommandExecutionException">Throw when the command fails to execute for any reason.</exception>
    Task DeleteBatchAsync(IEnumerable<TKey> keys, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a memory record into the data store. Does not guarantee that the collection exists.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="record">The memory record to upsert.</param>
    /// <param name="options">Optional options for upserting the record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifier for the memory record.</returns>
    /// <exception cref="MemoryServiceCommandExecutionException">Throw when the command fails to execute for any reason.</exception>
    /// <exception cref="MemoryDataModelMappingException">Throw when mapping between the storage model and data model fails.</exception>
    Task<TKey> UpsertAsync(TDataModel record, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a group of memory records into the data store. Does not guarantee that the collection exists.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// Upserts will be made in a single request or in a single parallel batch depending on the available store functionality.
    /// </summary>
    /// <param name="records">The memory records to upsert.</param>
    /// <param name="options">Optional options for upserting the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifiers for the memory records.</returns>
    /// <exception cref="MemoryServiceCommandExecutionException">Throw when the command fails to execute for any reason.</exception>
    /// <exception cref="MemoryDataModelMappingException">Throw when mapping between the storage model and data model fails.</exception>
    IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TDataModel> records, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default);
}
