// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Options when creating a <see cref="RedisVectorStore"/>.
/// </summary>
public sealed class RedisVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="RedisVectorStoreRecordCollection{TRecord}"/> instances, if custom options are required.
    /// </summary>
    public IRedisVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
