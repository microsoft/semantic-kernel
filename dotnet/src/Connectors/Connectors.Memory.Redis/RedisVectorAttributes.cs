// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Memory.Redis;

/// <summary>
/// Vector similarity index algorithm. Supported algorithms are {FLAT, HNSW}. The default value is "HNSW".
/// <see href="https://redis.io/docs/interact/search-and-query/search/vectors/#create-a-vector-field"/>
/// </summary>
public enum VectorIndexAlgorithms
{
    FLAT,
    HNSW,
}

/// <summary>
/// Vector type. Supported types are {FLOAT32, FLOAT64}. The default value is "FLOAT32".
/// </summary>
#pragma warning disable CA1720
public enum VectorTypes
{
    FLOAT32,
    FLOAT64,
}

/// <summary>
/// Supported distance metrics are {L2, IP, COSINE}. The default value is "COSINE".
/// </summary>
public enum VectorDistanceMetrics
{
    L2,
    IP,
    COSINE,
}
