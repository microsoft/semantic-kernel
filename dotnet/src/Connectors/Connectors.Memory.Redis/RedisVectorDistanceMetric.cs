// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Supported distance metrics are {L2, IP, COSINE}. The default value is "COSINE".
/// <see href="https://redis.io/docs/interact/search-and-query/search/vectors/"/>
/// </summary>
[Experimental("SKEXP0020")]
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
