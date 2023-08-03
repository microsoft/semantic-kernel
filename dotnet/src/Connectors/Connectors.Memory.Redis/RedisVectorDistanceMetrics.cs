// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Memory.Redis;

/// <summary>
/// Supported distance metrics are {L2, IP, COSINE}. The default value is "COSINE".
/// <see href="https://redis.io/docs/interact/search-and-query/search/vectors/"/>
/// </summary>
public enum VectorDistanceMetrics
{
    /// <summary>
    /// Euclidean distance between two vectors
    /// </summary>
    L2,

    /// <summary>
    /// Inner product of two vectors
    /// </summary>
    IP,

    /// <summary>
    /// Cosine distance of two vectors
    /// </summary>
    COSINE,
}
