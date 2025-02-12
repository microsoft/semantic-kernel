// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines an interface for accessing the list of collections in a vector store.
/// </summary>
/// <remarks>
/// This interface can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public interface IVectorStore
{
    /// <summary>
    /// Gets a collection from the vector store.
    /// </summary>
    /// <typeparam name="TKey">The data type of the record key.</typeparam>
    /// <typeparam name="TRecord">The record data model to use for adding, updating, and retrieving data from the collection.</typeparam>
    /// <param name="name">The name of the collection.</param>
    /// <param name="vectorStoreRecordDefinition">The schema of the record type.</param>
    /// <returns>A new <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> instance for managing the records in the collection.</returns>
    /// <remarks>
    /// To successfully request a collection, either <typeparamref name="TRecord"/> must be annotated with attributes that define the schema of
    /// the record type, or <paramref name="vectorStoreRecordDefinition"/> must be provided.
    /// </remarks>
    /// <seealso cref="VectorStoreRecordKeyAttribute"/>
    /// <seealso cref="VectorStoreRecordDataAttribute"/>
    /// <seealso cref="VectorStoreRecordVectorAttribute"/>
    IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull;

    /// <summary>
    /// Retrieves the names of all the collections in the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The list of names of all the collections in the vector store.</returns>
    IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default);
}
