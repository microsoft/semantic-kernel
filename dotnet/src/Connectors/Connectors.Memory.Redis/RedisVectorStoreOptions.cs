// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Options when creating a <see cref="RedisVectorStore"/>.
/// </summary>
public sealed class RedisVectorStoreOptions
{
    internal static readonly RedisVectorStoreOptions Default = new();

    /// <summary>
    /// Indicates the way in which data should be stored in redis. Default is <see cref="RedisStorageType.Json"/>.
    /// </summary>
    public RedisStorageType? StorageType { get; set; } = RedisStorageType.Json;

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
