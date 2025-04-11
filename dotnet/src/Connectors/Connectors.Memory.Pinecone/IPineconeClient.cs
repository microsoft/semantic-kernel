// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Interface for a Pinecone client
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
public interface IPineconeClient
{
    /// <summary>
    /// Get vectors by id
    /// </summary>
    /// <param name="indexName"> the name of the index </param>
    /// <param name="ids"> A list of ids</param>
    /// <param name="indexNamespace"> The namespace to use</param>
    /// <param name="includeValues"> Whether to include the vector values</param>
    /// <param name="cancellationToken"> The cancellation token</param>
    /// <returns> A list of vector records</returns>
    IAsyncEnumerable<PineconeDocument?> FetchVectorsAsync(
        string indexName,
        IEnumerable<string> ids,
        string indexNamespace = "",
        bool includeValues = false,
        CancellationToken cancellationToken = default
    );

    /// <summary>
    /// Gets the most relevant vectors to a list of queries
    /// </summary>
    /// <param name="indexName"> the name of the index </param>
    /// <param name="query"> the query parameters</param>
    /// <param name="includeValues"> whether to include the vector values</param>
    /// <param name="includeMetadata"> whether to include the metadata</param>
    /// <param name="cancellationToken"></param>
    /// <returns> a list of query matches</returns>
    IAsyncEnumerable<PineconeDocument?> QueryAsync(
        string indexName,
        Query query,
        bool includeValues = false,
        bool includeMetadata = true,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Find the nearest vectors in a collection using vector similarity search.
    /// </summary>
    /// <param name="indexName"> the name of the index </param>
    /// <param name="vector">The vector to compare the collection's vectors with.</param>
    /// <param name="threshold">The minimum relevance threshold for returned results.</param>
    /// <param name="topK">The maximum number of similarity results to return.</param>
    /// <param name="includeValues"> Whether to include the vector values</param>
    /// <param name="includeMetadata"> Whether to include the metadata</param>
    /// <param name="indexNamespace">The name assigned to a collection of vectors.</param>
    /// <param name="filter"> A filter to apply to the results</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    IAsyncEnumerable<(PineconeDocument, double)> GetMostRelevantAsync(
        string indexName,
        ReadOnlyMemory<float> vector,
        double threshold,
        int topK,
        bool includeValues,
        bool includeMetadata,
        string indexNamespace = "",
        Dictionary<string, object>? filter = default,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a list of documents
    /// </summary>
    /// <param name="indexName"> the name of the index</param>
    /// <param name="vectors"> the list of documents</param>
    /// <param name="indexNamespace"> the namespace to use</param>
    /// <param name="cancellationToken"></param>
    Task<int> UpsertAsync(
        string indexName,
        IEnumerable<PineconeDocument> vectors,
        string indexNamespace = "",
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete
    /// </summary>
    /// <remarks>
    /// The Delete operation deletes vectors, by id, from a single namespace. It's possible to delete items by their id, from a single namespace.
    /// </remarks>
    /// <param name="indexName"> The name of the index</param>
    /// <param name="ids"> The ids to delete</param>
    /// <param name="indexNamespace"> The namespace to use</param>
    /// <param name="filter"> The filter to use</param>
    /// <param name="deleteAll"> Whether to delete all vectors</param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of Object</returns>
    Task DeleteAsync(
        string indexName,
        IEnumerable<string>? ids = null,
        string indexNamespace = "",
        Dictionary<string, object>? filter = null,
        bool deleteAll = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Updates a vector
    /// </summary>
    /// <remarks>
    /// The Update operation updates vector in a namespace. If a value is included, it will overwrite the previous value. If a set_metadata is included, the values of the fields specified in it will be added or overwrite the previous value.
    /// </remarks>
    /// <param name="indexName"> The name of the index</param>
    /// <param name="document"> The document to update</param>
    /// <param name="indexNamespace"> The namespace to use</param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of Object</returns>
    Task UpdateAsync(
        string indexName,
        PineconeDocument document,
        string indexNamespace = "",
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Describe Index Stats
    /// </summary>
    /// <remarks>
    /// The DescribeIndexStats operation returns statistics about the index's contents, including the vector count per namespace and the number of dimensions.
    /// </remarks>
    /// <param name="indexName"> the name of the index</param>
    /// <param name="filter"> a filter to use </param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns> the index stats</returns>
    Task<IndexStats?> DescribeIndexStatsAsync(
        string indexName,
        Dictionary<string, object>? filter = default,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// List indexes
    /// </summary>
    /// <remarks>
    /// This operation returns a list of your Pinecone index names.
    /// </remarks>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns> A list of index names</returns>
    IAsyncEnumerable<string?> ListIndexesAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete Index
    /// </summary>
    /// <remarks>
    /// This operation deletes an existing index.
    /// </remarks>
    /// <param name="indexName"> the name of the index.</param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of void</returns>
    Task DeleteIndexAsync(string indexName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Check if a vector collection exists.
    /// </summary>
    /// <param name="indexName">The name assigned to a collection of vectors.</param>
    /// <param name="cancellationToken">Cancellation Token.</param>
    Task<bool> DoesIndexExistAsync(string indexName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Describe index
    /// </summary>
    /// <remarks>
    /// Get a description of an index.
    /// </remarks>
    /// <param name="indexName"> the name of the index.</param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of Index</returns>
    Task<PineconeIndex?> DescribeIndexAsync(string indexName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Create index
    /// </summary>
    /// <remarks>
    /// This operation creates a Pinecone index. It's possible to use it to specify the measure of similarity, the dimension of vectors to be stored in the index, the numbers of replicas to use, and more.
    /// </remarks>
    /// <param name="indexDefinition">  the configuration of the index.</param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of void</returns>
    Task CreateIndexAsync(IndexDefinition indexDefinition, CancellationToken cancellationToken = default);

    /// <summary>
    /// Configure index
    /// </summary>
    /// <remarks>
    /// This operation specifies the pod type and number of replicas for an index.
    /// </remarks>
    /// <param name="indexName"> the name of the index.</param>
    /// <param name="replicas"> the number of replicas to use.</param>
    /// <param name="podType"> the pod type to use.</param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of void</returns>
    Task ConfigureIndexAsync(string indexName, int replicas = 1, PodType podType = PodType.P1X1, CancellationToken cancellationToken = default);
}
