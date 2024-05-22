// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// An interface for adding, updating, deleting and retrieving records from a vector store.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <typeparam name="TDataModel">The data model to use for adding, updating and retrieving data from storage.</typeparam>
[Experimental("SKEXP0001")]
public interface IVectorDBRecordService<TKey, TDataModel>
    where TDataModel : class
{
    /// <summary>
    /// Gets a vector record from the data store. Does not guarantee that the collection exists.
    /// Throws if the record is not found.
    /// </summary>
    /// <param name="key">The unique id associated with the vector record to get.</param>
    /// <param name="options">Optional options for retrieving the record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The vector record if found, otherwise null.</returns>
    Task<TDataModel?> GetAsync(TKey key, GetRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a batch of vector records from the data store. Does not guarantee that the collection exists.
    /// Throws if any of the records are not found.
    /// Gets will be made in a single request or in a single parallel batch depending on the available store functionality.
    /// </summary>
    /// <param name="keys">The unique ids associated with the vector record to get.</param>
    /// <param name="options">Optional options for retrieving the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The vector records associated with the unique keys provided.</returns>
    IAsyncEnumerable<TDataModel?> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Removes a vector record from the data store. Does not guarantee that the collection exists.
    /// </summary>
    /// <param name="key">The unique id associated with the vector record to remove.</param>
    /// <param name="options">Optional options for removing the record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifier for the vector record.</returns>
    Task RemoveAsync(TKey key, RemoveRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Removes a batch of vector records from the data store. Does not guarantee that the collection exists.
    /// Removes will be made in a single request or in a single parallel batch depending on the available store functionality.
    /// </summary>
    /// <param name="keys">The unique ids associated with the vector records to remove.</param>
    /// <param name="options">Optional options for removing the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task RemoveBatchAsync(IEnumerable<TKey> keys, RemoveRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a vector record into the data store. Does not guarantee that the collection exists.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="record">The vector record to upsert.</param>
    /// <param name="options">Optional options for upserting the record.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifier for the vector record.</returns>
    Task<TKey> UpsertAsync(TDataModel record, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a group of vector records into the data store. Does not guarantee that the collection exists.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// Upserts will be made in a single request or in a single parallel batch depending on the available store functionality.
    /// </summary>
    /// <param name="records">The vector records to upsert.</param>
    /// <param name="options">Optional options for upserting the records.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The unique identifiers for the vector records.</returns>
    IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TDataModel> records, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default);
}
