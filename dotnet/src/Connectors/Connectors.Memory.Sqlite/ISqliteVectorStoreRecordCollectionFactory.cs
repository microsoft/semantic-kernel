// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Interface for constructing <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> SQLite instances when using <see cref="IVectorStore"/> to retrieve these.
/// </summary>
[Obsolete("To control how collections are instantiated, extend your provider's IVectorStore implementation and override GetCollection()")]
public interface ISqliteVectorStoreRecordCollectionFactory
{
    /// <summary>
    /// Constructs a new instance of the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.
    /// </summary>
    /// <typeparam name="TKey">The data type of the record key.</typeparam>
    /// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
    /// <param name="connectionString">The connection string for the SQLite database represented by this <see cref="SqliteVectorStore"/>.</param>
    /// <param name="name">The name of the collection to connect to.</param>
    /// <param name="vectorStoreRecordDefinition">An optional record definition that defines the schema of the record type. If not present, attributes on <typeparamref name="TRecord"/> will be used.</param>
    /// <returns>The new instance of <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</returns>
    IVectorStoreRecordCollection<TKey, TRecord> CreateVectorStoreRecordCollection<TKey, TRecord>(
        string connectionString,
        string name,
        VectorStoreRecordDefinition? vectorStoreRecordDefinition)
        where TKey : notnull
        where TRecord : notnull;
}
