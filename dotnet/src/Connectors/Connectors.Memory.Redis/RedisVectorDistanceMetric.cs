// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Supported distance metrics are {L2, IP, COSINE}. The default value is "COSINE".
/// <see href="https://redis.io/docs/interact/search-and-query/search/vectors/"/>
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and RedisVectorStore")]
public enum VectorDistanceMetric
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
