// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Interface for accessing the list of collections in a vector store.
/// </summary>
/// <remarks>
/// This interface can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
[Experimental("SKEXP0001")]
public interface IVectorStore
{
    /// <summary>
    /// Get a collection from the vector store.
    /// </summary>
    /// <typeparam name="TKey">The data type of the record key.</typeparam>
    /// <typeparam name="TRecord">The record data model to use for adding, updating and retrieving data from the collection.</typeparam>
    /// <param name="name">The name of the collection.</param>
    /// <param name="vectorStoreRecordDefinition">Defines the schema of the record type.</param>
    /// <returns>A new <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> instance for managing the records in the collection.</returns>
    /// <remarks>
    /// To successfully request a collection, either <typeparamref name="TRecord"/> must be annotated with attributes that define the schema of
    /// the record type, or <paramref name="vectorStoreRecordDefinition"/> must be provided.
    /// </remarks>
    /// <seealso cref="VectorStoreRecordKeyAttribute"/>
    /// <seealso cref="VectorStoreRecordDataAttribute"/>
    /// <seealso cref="VectorStoreRecordVectorAttribute"/>
    IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicConstructors | DynamicallyAccessedMemberTypes.PublicProperties)] TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
        where TRecord : class;

    /// <summary>
    /// Retrieve the names of all the collections in the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The list of names of all the collections in the vector store.</returns>
    IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default);
}
