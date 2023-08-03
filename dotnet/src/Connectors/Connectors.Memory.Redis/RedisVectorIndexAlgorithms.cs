// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Memory.Redis;

/// <summary>
/// Vector similarity index algorithm. Supported algorithms are {FLAT, HNSW}. The default value is "HNSW".
/// <see href="https://redis.io/docs/interact/search-and-query/search/vectors/#create-a-vector-field"/>
/// </summary>
public enum VectorIndexAlgorithms
{
    /// <summary>
    /// Indexing by brute-force
    /// </summary>
    FLAT,

    /// <summary>
    /// Indexing by the Hierarchical Navigable Small World algorithm
    /// </summary>
    HNSW,
}
