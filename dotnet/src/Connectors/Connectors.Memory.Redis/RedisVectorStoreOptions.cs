// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Options when creating a <see cref="RedisVectorStore"/>.
/// </summary>
public sealed class RedisVectorStoreOptions
{
    /// <summary>
<<<<<<< HEAD
    /// An optional factory to use for constructing <see cref="RedisJsonVectorStoreRecordCollection{TRecord}"/> instances, if a custom record collection is required.
=======
    /// An optional factory to use for constructing <see cref="RedisJsonVectorStoreRecordCollection{TRecord}"/> instances, if custom options are required.
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
    /// </summary>
    public IRedisVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }

    /// <summary>
    /// Indicates the way in which data should be stored in redis. Default is <see cref="RedisStorageType.Json"/>.
    /// </summary>
    public RedisStorageType? StorageType { get; init; } = RedisStorageType.Json;
}
