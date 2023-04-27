// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone;

/// <summary>
///  Interface for Pinecone memory store that extends the memory store interface
///  to add support for namespaces
/// </summary>
public interface IPineconeMemoryStore : IMemoryStore
{

    /// <summary>
    /// Upserts a memory record into the data store in the given namespace.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="nameSpace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="record">The memory record to upsert.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>The unique identifier for the memory record.</returns>
    Task<string> UpsertToNamespaceAsync(
        string indexName,
        string nameSpace,
        MemoryRecord record,
        CancellationToken cancel = default);

    /// <summary>
    /// Upserts a group of memory records into the data store in the given namespace.
    ///     If the record already exists, it will be updated.
    ///     If the record does not exist, it will be created.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of vectors.</param>
    /// <param name="nameSpace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="records">The memory records to upsert.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>The unique identifiers for the memory records.</returns>
    IAsyncEnumerable<string> UpsertBatchToNamespaceAsync(
        string indexName,
        string nameSpace,
        IEnumerable<MemoryRecord> records,
        CancellationToken cancel = default);

    /// <summary>
    /// Gets a memory record from the data store in the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="nameSpace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="key">The unique id associated with the memory record to get.</param>
    /// <param name="withEmbedding">If true, the embedding will be returned in the memory record.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>The memory record if found, otherwise null.</returns>
    Task<MemoryRecord?> GetFromNamespaceAsync(
        string indexName,
        string nameSpace,
        string key,
        bool withEmbedding = false,
        CancellationToken cancel = default);

    /// <summary>
    /// Gets a batch of memory records from the data store in the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embedding.</param>
    /// <param name="nameSpace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="keys">The unique ids associated with the memory record to get.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>The memory records associated with the unique keys provided.</returns>
    IAsyncEnumerable<MemoryRecord> GetBatchFromNamespaceAsync(
        string indexName,
        string nameSpace,
        IEnumerable<string> keys,
        bool withEmbeddings = false,
        CancellationToken cancel = default);

    /// <summary>
    ///  Gets the memory records associated with the given document id.
    /// </summary>
    /// <param name="indexName"> the name of the index to search.</param>
    /// <param name="documentId"> the document id to search for.</param>
    /// <param name="limit"> the number of results to return.</param>
    /// <param name="nameSpace"> the namespace to search.</param>
    /// <param name="withEmbedding"> if true, the embedding will be returned in the memory record.</param>
    /// <param name="cancel"></param>
    /// <returns> the memory records associated with the document id provided.</returns>
    IAsyncEnumerable<MemoryRecord?> GetWithDocumentIdAsync(
        string indexName,
        string documentId,
        int limit = 3,
        string nameSpace = "",
        bool withEmbedding = false,
        CancellationToken cancel = default);

    /// <summary>
    /// Gets the memory records associated with the given document ids.
    /// </summary>
    /// <param name="indexName">  the name of the index to search.</param>
    /// <param name="documentIds"> the document ids to search for.</param>
    /// <param name="limit"> the number of results to return.</param>
    /// <param name="nameSpace"> the namespace to search.</param>
    /// <param name="withEmbeddings"> if true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancel"></param>
    /// <returns> the memory records associated with the document ids provided.</returns>
    IAsyncEnumerable<MemoryRecord?> GetWithDocumentIdBatchAsync(
        string indexName,
        IEnumerable<string> documentIds,
        int limit = 3,
        string nameSpace = "",
        bool withEmbeddings = false,
        CancellationToken cancel = default);

    /// <summary>
    ///  Gets a memory record from the data store that matches the filter.
    /// </summary>
    /// <param name="indexName"> the name of the index to search.</param>
    /// <param name="filter"> the filter to apply to the search.</param>
    /// <param name="limit"> the number of results to return.</param>
    /// <param name="nameSpace"> the namespace to search.</param>
    /// <param name="withEmbeddings"> if true, the embedding will be returned in the memory record.</param>
    /// <param name="cancel"></param>
    /// <returns> the memory records that match the filter.</returns>
    public IAsyncEnumerable<MemoryRecord?> GetBatchWithFilterAsync(
        string indexName,
        Dictionary<string, object> filter,
        int limit = 10,
        string nameSpace = "",
        bool withEmbeddings = false,
        CancellationToken cancel = default);

    /// <summary>
    /// Removes a memory record from the data store in the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="nameSpace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="key">The unique id associated with the memory record to remove.</param>
    /// <param name="cancel">Cancellation token.</param>
    Task RemoveFromNamespaceAsync(
        string indexName,
        string nameSpace,
        string key,
        CancellationToken cancel = default);

    /// <summary>
    /// Removes a batch of memory records from the data store in the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="nameSpace"> The namespace to remove the memory records from.</param>
    /// <param name="keys">The unique ids associated with the memory record to remove.</param>
    /// <param name="cancel">Cancellation token.</param>
    Task RemoveBatchFromNamespaceAsync(
        string indexName,
        string nameSpace,
        IEnumerable<string> keys,
        CancellationToken cancel = default);

    /// <summary>
    ///  Removes memory records from the data store associated with the document id.
    /// </summary>
    /// <param name="indexName"> the name of the index to remove from.</param>
    /// <param name="documentId">  the document id to remove.</param>
    /// <param name="nameSpace"> the namespace to remove from.</param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    Task RemoveWithDocumentIdAsync(
        string indexName,
        string documentId,
        string nameSpace = "",
        CancellationToken cancel = default);

    /// <summary>
    ///  Removes memory records from the data store that match the document ids.
    /// </summary>
    /// <param name="indexName"> the name of the index to remove from.</param>
    /// <param name="documentIds"> the document ids to remove.</param>
    /// <param name="nameSpace"> the namespace to remove from.</param>
    /// <param name="cancel"></param>
    /// <returns></returns>
    public Task RemoveWithDocumentIdBatchAsync(
        string indexName,
        IEnumerable<string> documentIds,
        string nameSpace = "",
        CancellationToken cancel = default);

    /// <summary>
    ///  Removes memory records from the data store that match the filter.
    /// </summary>
    /// <param name="indexName"> the name of the index to remove from.</param>
    /// <param name="filter"> the filter to apply to the search.</param>
    /// <param name="nameSpace"> the namespace to remove from.</param>
    /// <param name="cancel"></param>
    /// <remarks>
    ///  In the same way that you can filter your vector search results, you can also filter your vector deletion.
    /// </remarks>
    Task RemoveWithFilterAsync(
        string indexName,
        Dictionary<string, object> filter,
        string nameSpace = "",
        CancellationToken cancel = default);

    /// <summary>
    /// Gets the nearest filtered matches to the <see cref="Embedding"/> of type <see cref="float"/>
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="embedding">The <see cref="Embedding"/> to compare the collection's embeddings with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="filter"> The filter to apply to the collection.</param>
    /// <param name="minRelevanceScore"></param>
    /// <param name="nameSpace"></param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>A group of tuples where item1 is a <see cref="MemoryRecord"/> and item2 is its similarity score as a <see cref="double"/>.</returns>
    /// <remarks>
    ///  from https://docs.pinecone.io/docs/metadata-filtering#supported-metadata-types
    /// You can limit your vector search based on metadata. Pinecone lets you attach metadata key-value pairs to vectors in an index,
    /// and specify filter expressions when you query the index. Searches with metadata filters retrieve exactly the number of
    /// nearest-neighbor results that match the filters.For most cases, the search latency will be even lower than unfiltered searches.
    /// </remarks>
    IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesWithFilterAsync(
        string indexName,
        Embedding<float> embedding,
        int limit,
        Dictionary<string, object> filter,
        double minRelevanceScore = 0.0,
        string nameSpace = "",
        bool withEmbeddings = false,
        CancellationToken cancel = default);

    /// <summary>
    /// Gets the nearest matches to the <see cref="Embedding"/> of type <see cref="float"/> from the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="nameSpace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="embedding">The <see cref="Embedding"/> to compare the collection's embeddings with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns>A group of tuples where item1 is a <see cref="MemoryRecord"/> and item2 is its similarity score as a <see cref="double"/>.</returns>
    IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesFromNamespaceAsync(
        string indexName,
        string nameSpace,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0.0,
        bool withEmbeddings = false,
        CancellationToken cancel = default);

    /// <summary>
    /// Gets the nearest match to the <see cref="Embedding"/> of type <see cref="float"/> from the given namespace.
    /// </summary>
    /// <param name="indexName">The name associated with a collection of embeddings.</param>
    /// <param name="nameSpace"> The namespace associated with a collection of embeddings.</param>
    /// <param name="embedding">The <see cref="Embedding"/> to compare the collection's embeddings with.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="withEmbedding">If true, the embedding will be returned in the memory record.</param>
    /// <param name="cancel">Cancellation token</param>
    /// <returns>A tuple consisting of the <see cref="MemoryRecord"/> and the similarity score as a <see cref="double"/>. Null if no nearest match found.</returns>
    Task<(MemoryRecord, double)?> GetNearestMatchFromNamespaceAsync(
        string indexName,
        string nameSpace,
        Embedding<float> embedding,
        double minRelevanceScore = 0.0,
        bool withEmbedding = false,
        CancellationToken cancel = default);

    /// <summary>
    ///  Clears all vectors in the given namespace.
    /// </summary>
    /// <param name="indexName"></param>
    /// <param name="nameSpace"></param>
    /// <param name="cancellationToken"></param>
    Task ClearNamespaceAsync(string indexName, string nameSpace, CancellationToken cancellationToken = default);

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
