// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Memory.Redis;

/// <summary>
/// Vector type. Supported types are {FLOAT32, FLOAT64}. The default value is "FLOAT32".
/// <see href="https://redis.io/docs/interact/search-and-query/search/vectors/#creation-attributes-per-algorithm"/>
/// </summary>
#pragma warning disable CA1720  // Identifiers should not contain type names
public enum VectorTypes
{
    /// <summary>
    /// Vectors of 32-bit floats
    /// </summary>
    FLOAT32,

    /// <summary>
    /// Vectors of 64-bit floats (doubles)
    /// </summary>
    FLOAT64,
}
