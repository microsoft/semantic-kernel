// Copyright (c) Kevin BEAUGRAND. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.MssqlServer;

/// <summary>
/// Interface for a client that interacts with a SQL Server database to store and retrieve data.
/// </summary>
public interface ISqlServerClient : IDisposable
{
    /// <summary>
    /// Creates a new collection with the specified name in the SQL Server database.
    /// </summary>
    /// <param name="collectionName">The name of the collection to create.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Creates the necessary tables in the SQL Server database for the client to function properly.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    Task CreateTablesAsync(CancellationToken cancellationToken);

    /// <summary>
    /// Deletes a document from the specified collection in the SQL Server database.
    /// </summary>
    /// <param name="collectionName">The name of the collection to delete the document from.</param>
    /// <param name="key">The key of the document to delete.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
    /// <returns>A task that represents the asynchronous delete operation.</returns>
    Task DeleteAsync(string collectionName, string key, CancellationToken cancellationToken = default);
    /// <summary>
    /// Deletes a batch of documents from the specified collection in the SQL Server database.
    /// </summary>
    /// <param name="collectionName">The name of the collection to delete documents from.</param>
    /// <param name="keys">The keys of the documents to delete.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    Task DeleteBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default);
    /// <summary>
    /// Deletes a collection with the specified name from the SQL Server database asynchronously.
    /// </summary>
    /// <param name="collectionName">The name of the collection to delete.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the asynchronous operation.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default);
    /// <summary>
    /// Determines whether a collection with the specified name exists in the SQL Server database.
    /// </summary>
    /// <param name="collectionName">The name of the collection to check for existence.</param>
    /// <param name="cancellationToken">A cancellation token to observe while waiting for the task to complete.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains a value indicating whether the collection exists.</returns>
    Task<bool> DoesCollectionExistsAsync(string collectionName, CancellationToken cancellationToken = default);
    /// <summary>
    /// Gets a list of all collections in the SQL Server database.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token to observe while waiting for the task to complete.</param>
    /// <returns>An asynchronous enumerable of collection names.</returns>
    IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default);
    /// <summary>
    /// Retrieves the nearest matches to the specified embedding in the specified collection.
    /// </summary>
    /// <param name="collectionName">The name of the collection to search in.</param>
    /// <param name="embedding">The embedding to search for.</param>
    /// <param name="limit">The maximum number of matches to retrieve.</param>
    /// <param name="minRelevanceScore">The minimum relevance score for a match to be considered relevant.</param>
    /// <param name="withEmbeddings">Whether to include embeddings in the results.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
    /// <returns>An asynchronous enumerable of tuples containing the matching entries and their relevance scores.</returns>
    IAsyncEnumerable<(SqlServerMemoryEntry, double)> GetNearestMatchesAsync(string collectionName, string embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default);
    /// <summary>
    /// Reads a <see cref="SqlServerMemoryEntry"/> from the specified collection with the given key.
    /// </summary>
    /// <param name="collectionName">The name of the collection to read from.</param>
    /// <param name="key">The key of the entry to read.</param>
    /// <param name="withEmbeddings">Whether to include embeddings in the returned entry.</param>
    /// <param name="cancellationToken">A <see cref="CancellationToken"/> to observe while waiting for the task to complete.</param>
    /// <returns>A <see cref="Task{TResult}"/> representing the asynchronous operation. The task result contains the <see cref="SqlServerMemoryEntry"/> read from the collection, or null if no entry was found with the given key.</returns>
    Task<SqlServerMemoryEntry?> ReadAsync(string collectionName, string key, bool withEmbeddings = false, CancellationToken cancellationToken = default);
    /// <summary>
    /// Asynchronously reads a batch of <see cref="SqlServerMemoryEntry"/> objects from the specified collection in the SQL Server database.
    /// </summary>
    /// <param name="collectionName">The name of the collection to read from.</param>
    /// <param name="keys">The keys of the <see cref="SqlServerMemoryEntry"/> objects to read.</param>
    /// <param name="withEmbeddings">Whether to include embeddings in the <see cref="SqlServerMemoryEntry"/> objects.</param>
    /// <param name="cancellationToken">A <see cref="CancellationToken"/> to observe while waiting for the task to complete.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> of <see cref="SqlServerMemoryEntry"/> objects.</returns>
    IAsyncEnumerable<SqlServerMemoryEntry> ReadBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, CancellationToken cancellationToken = default);
    /// <summary>
    /// Upserts a document with the specified key and embedding into the specified collection.
    /// </summary>
    /// <param name="collectionName">The name of the collection to upsert the document into.</param>
    /// <param name="key">The key of the document to upsert.</param>
    /// <param name="metadata">The metadata of the document to upsert.</param>
    /// <param name="embedding">The embedding of the document to upsert.</param>
    /// <param name="timestamp">The timestamp of the document to upsert.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A task that represents the asynchronous upsert operation.</returns>
    Task UpsertAsync(string collectionName, string key, string? metadata, string embedding, DateTimeOffset? timestamp, CancellationToken cancellationToken = default);
}
