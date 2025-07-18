// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Indicates the way in which data is stored in redis.
/// </summary>
public enum RedisStorageType
{
    /// <summary>
    /// Data is stored as JSON.
    /// </summary>
    Json,

    /// <summary>
    /// Data is stored as collections of field-value pairs.
    /// </summary>
    HashSet
}
