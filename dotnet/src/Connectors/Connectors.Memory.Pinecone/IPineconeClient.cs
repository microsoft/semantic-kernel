using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone;

public interface IPineconeClient
{
    /// <summary>
    ///  The name of the index this client is connected to
    /// </summary>
    public string IndexName { get; }

    /// <summary>
    ///  The host this client is connected to which is unique to the index
    /// </summary>
    public string Host { get; }

    /// <summary>
    ///  The port this client is connected to
    /// </summary>
    public int Port { get; }

    /// <summary>
    /// The state of the index
    /// </summary>
    /// <remarks>
    /// Important to make sure the index is ready before querying when initializing
    ///  a new index. This is because a new index can a few minutes to be ready for use.
    /// </remarks>
    public IndexState State { get; }

    /// <summary>
    ///  Whether the index is ready for use
    /// </summary>
    public bool Ready { get; }

    /// <summary>
    ///  Get vectors by id
    /// </summary>
    /// <param name="indexName"></param>
    /// <param name="ids"> A list of ids</param>
    /// <param name="nameSpace"> The namespace to use</param>
    /// <param name="includeValues"></param>
    /// <param name="cancellationToken"> The cancellation token</param>
    /// <returns> A list of vector records</returns>
    public IAsyncEnumerable<PineconeDocument?> FetchVectorsAsync(
        string indexName,
        IEnumerable<string> ids,
        string nameSpace = "",
        bool includeValues = false,
        CancellationToken cancellationToken = default
    );

    /// <summary>
    ///  Gets the most relevant vectors to a list of queries
    /// </summary>
    /// <param name="indexName"></param>
    /// <param name="vector"></param>
    /// <param name="topK"> the number of results to return</param>
    /// <param name="nameSpace"> the namespace to use</param>
    /// <param name="includeValues"> whether to include the vector values</param>
    /// <param name="includeMetadata"> whether to include the metadata</param>
    /// <param name="filter"></param>
    /// <param name="sparseVector"></param>
    /// <param name="id"></param>
    /// <param name="cancellationToken"></param>
    /// <returns> a list of query matches</returns>
    public IAsyncEnumerable<PineconeDocument?> QueryAsync(
        string indexName,
        IEnumerable<float> vector,
        bool includeValues,
        bool includeMetadata,
        int topK,
        string nameSpace = "",
        Dictionary<string, object>? filter = default,
        SparseVectorData? sparseVector = default,
        string? id = default,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Find the nearest vectors in a collection using vector similarity search.
    /// </summary>
    /// <param name="indexName"></param>
    /// <param name="vector">The vector to compare the collection's vectors with.</param>
    /// <param name="threshold">The minimum relevance threshold for returned results.</param>
    /// <param name="topK">The maximum number of similarity results to return.</param>
    /// <param name="nameSpace">The name assigned to a collection of vectors.</param>
    /// <param name="includeValues"></param>
    /// <param name="includeMetadata"></param>
    /// <param name="filter"></param>
    /// <param name="cancellationToken">Cancellation token.</param>
    public IAsyncEnumerable<(PineconeDocument, double)> GetMostRelevantAsync(
        string indexName,
        IEnumerable<float> vector,
        double threshold,
        int topK,
        bool includeValues,
        bool includeMetadata,
        string? nameSpace = "",
        Dictionary<string, object>? filter = default,
        CancellationToken cancellationToken = default);

    /// <summary>
    ///  Upserts a list of documents
    /// </summary>
    /// <param name="indexName"></param>
    /// <param name="vectors"> the list of documents</param>
    /// <param name="nameSpace"> the namespace to use</param>
    /// <param name="cancellationToken"></param>
    Task<int> UpsertAsync(
        string indexName,
        IEnumerable<PineconeDocument> vectors,
        string nameSpace = "",
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete
    /// </summary>
    /// <remarks>
    /// The Delete operation deletes vectors, by id, from a single namespace. You can delete items by their id, from a single namespace.
    /// </remarks>
    /// <param name="indexName"></param>
    /// <param name="ids"></param>
    /// <param name="deleteAll"></param>
    /// <param name="nameSpace"></param>
    /// <param name="filter"></param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of Object</returns>
    Task DeleteAsync(
        string indexName,
        IEnumerable<string>? ids,
        string nameSpace = "",
        Dictionary<string, object>? filter = null,
        bool deleteAll = false,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Fetch
    /// </summary>
    /// <remarks>
    /// The Update operation updates vector in a namespace. If a value is included, it will overwrite the previous value. If a set_metadata is included, the values of the fields specified in it will be added or overwrite the previous value.
    /// </remarks>
    /// <param name="indexName"></param>
    /// <param name="document"></param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of Object</returns>
    Task UpdateAsync(
        string indexName,
        PineconeDocument document,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Describe Index Stats
    /// </summary>
    /// <remarks>
    /// The DescribeIndexStats operation returns statistics about the index&#39;s contents, including the vector count per namespace and the number of dimensions.
    /// </remarks>
    /// <param name="indexName"></param>
    /// <param name="filter"></param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of DescribeIndexStatsResponse</returns>
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
    /// <param name="indexName"></param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of void</returns>
    Task DeleteIndexAsync(string indexName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Check if a vector collection exists.
    /// </summary>
    /// <param name="indexName">The name assigned to a collection of vectors.</param>
    /// <param name="cancel">Cancellation Token.</param>
    public Task<bool> DoesIndexExistAsync(string indexName, CancellationToken cancel = default);

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
    /// This operation creates a Pinecone index. You can use it to specify the measure of similarity, the dimension of vectors to be stored in the index, the numbers of replicas to use, and more.
    /// </remarks>
    /// <param name="indexDefinition">  the configuration of the index.</param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of void</returns>
    Task<string?> CreateIndexAsync(IndexDefinition indexDefinition, CancellationToken cancellationToken = default);

    /// <summary>
    /// Configure index
    /// </summary>
    /// <remarks>
    /// This operation specifies the pod type and number of replicas for an index.
    /// </remarks>
    /// <param name="indexName"></param>
    /// <param name="replicas"></param>
    /// <param name="podType"></param>
    /// <param name="cancellationToken">Cancellation Token to cancel the request.</param>
    /// <returns>Task of void</returns>
    Task ConfigureIndexAsync(string indexName, int replicas = 1, PodType podType = PodType.P1X1, CancellationToken cancellationToken = default);
}
