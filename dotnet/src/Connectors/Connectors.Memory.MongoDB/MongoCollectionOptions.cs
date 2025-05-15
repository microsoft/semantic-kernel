// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Options when creating a <see cref="MongoCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class MongoCollectionOptions : VectorStoreCollectionOptions
{
    internal static readonly MongoCollectionOptions Default = new();

    /// <summary>
    /// Vector index name to use. If null, the default "vector_index" name will be used.
    /// </summary>
    public string VectorIndexName { get; set; } = MongoConstants.DefaultVectorIndexName;

    /// <summary>
    /// Full text search index name to use. If null, the default "full_text_search_index" name will be used.
    /// </summary>
    public string FullTextSearchIndexName { get; set; } = MongoConstants.DefaultFullTextSearchIndexName;

    /// <summary>
    /// Number of max retries for vector collection operation.
    /// </summary>
    public int MaxRetries { get; set; } = 5;

    /// <summary>
    /// Delay in milliseconds between retries for vector collection operation.
    /// </summary>
    public int DelayInMilliseconds { get; set; } = 1_000;

    /// <summary>
    /// Number of nearest neighbors to use during the vector search.
    /// Value must be less than or equal to 10000.
    /// Recommended value should be higher than number of documents to return.
    /// If not provided, "number of documents * 10" value will be used.
    /// </summary>
    public int? NumCandidates { get; set; }
}
