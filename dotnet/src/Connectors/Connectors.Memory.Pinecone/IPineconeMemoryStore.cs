// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// Interface for Pinecone memory store that extends the memory store interface
/// to add support for namespaces
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
public interface IPineconeMemoryStore : IMemoryStore
{
    /// <summary>
    /// Upserts a memory record into the data store in the given namespace.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="indexNamespace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="record">The memory record to upsert.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The unique identifier for the memory record.</returns>
    Task<string> UpsertToNamespaceAsync(
        string indexName,
        string indexNamespace,
        MemoryRecord record,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a group of memory records into the data store in the given namespace.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of vectors.</param>
    /// <param name="indexNamespace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="records">The memory records to upsert.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The unique identifiers for the memory records.</returns>
    IAsyncEnumerable<string> UpsertBatchToNamespaceAsync(
        string indexName,
        string indexNamespace,
        IEnumerable<MemoryRecord> records,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a memory record from the data store in the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="indexNamespace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="key">The unique id associated with the memory record to get.</param>
    /// <param name="withEmbedding">If true, the embedding will be returned in the memory record.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The memory record if found, otherwise null.</returns>
    Task<MemoryRecord?> GetFromNamespaceAsync(
        string indexName,
        string indexNamespace,
        string key,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets a batch of memory records from the data store in the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embedding.</param>
    /// <param name="indexNamespace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="keys">The unique ids associated with the memory record to get.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The memory records associated with the unique keys provided.</returns>
    IAsyncEnumerable<MemoryRecord> GetBatchFromNamespaceAsync(
        string indexName,
        string indexNamespace,
        IEnumerable<string> keys,
        bool withEmbeddings = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    ///  Gets the memory records associated with the given document id.
    /// </summary>
    /// <param name="indexName"> the name of the index to search.</param>
    /// <param name="documentId"> the document id to search for.</param>
    /// <param name="limit"> the number of results to return.</param>
    /// <param name="indexNamespace"> the namespace to search.</param>
    /// <param name="withEmbedding"> if true, the embedding will be returned in the memory record.</param>
    /// <param name="cancellationToken"></param>
    /// <returns> the memory records associated with the document id provided.</returns>
    IAsyncEnumerable<MemoryRecord?> GetWithDocumentIdAsync(
        string indexName,
        string documentId,
        int limit = 3,
        string indexNamespace = "",
        bool withEmbedding = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the memory records associated with the given document ids.
    /// </summary>
    /// <param name="indexName">  the name of the index to search.</param>
    /// <param name="documentIds"> the document ids to search for.</param>
    /// <param name="limit"> the number of results to return.</param>
    /// <param name="indexNamespace"> the namespace to search.</param>
    /// <param name="withEmbeddings"> if true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancellationToken"></param>
    /// <returns> the memory records associated with the document ids provided.</returns>
    IAsyncEnumerable<MemoryRecord?> GetWithDocumentIdBatchAsync(
        string indexName,
        IEnumerable<string> documentIds,
        int limit = 3,
        string indexNamespace = "",
        bool withEmbeddings = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    ///  Gets a memory record from the data store that matches the filter.
    /// </summary>
    /// <param name="indexName"> the name of the index to search.</param>
    /// <param name="filter"> the filter to apply to the search.</param>
    /// <param name="limit"> the number of results to return.</param>
    /// <param name="indexNamespace"> the namespace to search.</param>
    /// <param name="withEmbeddings"> if true, the embedding will be returned in the memory record.</param>
    /// <param name="cancellationToken"></param>
    /// <returns> the memory records that match the filter.</returns>
    IAsyncEnumerable<MemoryRecord?> GetBatchWithFilterAsync(
        string indexName,
        Dictionary<string, object> filter,
        int limit = 10,
        string indexNamespace = "",
        bool withEmbeddings = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Removes a memory record from the data store in the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="indexNamespace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="key">The unique id associated with the memory record to remove.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task RemoveFromNamespaceAsync(
        string indexName,
        string indexNamespace,
        string key,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Removes a batch of memory records from the data store in the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="indexNamespace"> The namespace to remove the memory records from.</param>
    /// <param name="keys">The unique ids associated with the memory record to remove.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task RemoveBatchFromNamespaceAsync(
        string indexName,
        string indexNamespace,
        IEnumerable<string> keys,
        CancellationToken cancellationToken = default);

    /// <summary>
    ///  Removes memory records from the data store associated with the document id.
    /// </summary>
    /// <param name="indexName"> the name of the index to remove from.</param>
    /// <param name="documentId">  the document id to remove.</param>
    /// <param name="indexNamespace"> the namespace to remove from.</param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task RemoveWithDocumentIdAsync(
        string indexName,
        string documentId,
        string indexNamespace = "",
        CancellationToken cancellationToken = default);

    /// <summary>
    ///  Removes memory records from the data store that match the document ids.
    /// </summary>
    /// <param name="indexName"> the name of the index to remove from.</param>
    /// <param name="documentIds"> the document ids to remove.</param>
    /// <param name="indexNamespace"> the namespace to remove from.</param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    Task RemoveWithDocumentIdBatchAsync(
        string indexName,
        IEnumerable<string> documentIds,
        string indexNamespace = "",
        CancellationToken cancellationToken = default);

    /// <summary>
    ///  Removes memory records from the data store that match the filter.
    /// </summary>
    /// <param name="indexName"> the name of the index to remove from.</param>
    /// <param name="filter"> the filter to apply to the search.</param>
    /// <param name="indexNamespace"> the namespace to remove from.</param>
    /// <param name="cancellationToken"></param>
    /// <remarks>
    ///  It's possible to filter vector deletion in the same way as filtering vector search results.
    /// </remarks>
    Task RemoveWithFilterAsync(
        string indexName,
        Dictionary<string, object> filter,
        string indexNamespace = "",
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the nearest filtered matches to an embedding of type <see cref="float"/>
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="embedding">The embedding to compare the collection's embeddings with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="filter"> The filter to apply to the collection.</param>
    /// <param name="minRelevanceScore"></param>
    /// <param name="indexNamespace"></param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A group of tuples where item1 is a <see cref="MemoryRecord"/> and item2 is its similarity score as a <see cref="double"/>.</returns>
    /// <remarks>
    ///  from https://docs.pinecone.io/docs/metadata-filtering#supported-metadata-types
    /// It's possible to limit vector search based on metadata. Pinecone allows to attach metadata key-value pairs to vectors in an index,
    /// and specify filter expressions when querying the index. Searches with metadata filters retrieve exactly the number of
    /// nearest-neighbor results that match the filters. For most cases, the search latency will be even lower than unfiltered searches.
    /// </remarks>
    IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesWithFilterAsync(
        string indexName,
        ReadOnlyMemory<float> embedding,
        int limit,
        Dictionary<string, object> filter,
        double minRelevanceScore = 0.0,
        string indexNamespace = "",
        bool withEmbeddings = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the nearest matches to an embedding of type <see cref="float"/> from the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="indexNamespace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="embedding">The embedding to compare the collection's embeddings with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A group of tuples where item1 is a <see cref="MemoryRecord"/> and item2 is its similarity score as a <see cref="double"/>.</returns>
    IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesFromNamespaceAsync(
        string indexName,
        string indexNamespace,
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0.0,
        bool withEmbeddings = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the nearest match to an embedding of type <see cref="float"/> from the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="indexNamespace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="embedding">The embedding to compare the collection's embeddings with.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="withEmbedding">If true, the embedding will be returned in the memory record.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>A tuple consisting of the <see cref="MemoryRecord"/> and the similarity score as a <see cref="double"/>. Null if no nearest match found.</returns>
    Task<(MemoryRecord, double)?> GetNearestMatchFromNamespaceAsync(
        string indexName,
        string indexNamespace,
        ReadOnlyMemory<float> embedding,
        double minRelevanceScore = 0.0,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    ///  Clears all vectors in the given namespace.
    /// </summary>
    /// <param name="indexName"> The name of the index.</param>
    /// <param name="indexNamespace"> The namespace to clear.</param>
    /// <param name="cancellationToken"></param>
    Task ClearNamespaceAsync(string indexName, string indexNamespace, CancellationToken cancellationToken = default);

    /// <summary>
    /// List Namespaces
    /// </summary>
    /// <remarks>
    /// This operation returns a list of all namespaces in the given index.
    /// </remarks>
    /// <param name="indexName"> The name of the index.</param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns> A list of namespaces.</returns>
    IAsyncEnumerable<string?> ListNamespacesAsync(string indexName, CancellationToken cancellationToken = default);
}
