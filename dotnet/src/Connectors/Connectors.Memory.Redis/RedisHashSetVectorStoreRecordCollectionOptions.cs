// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Options when creating a <see cref="RedisHashSetVectorStoreRecordCollectionOptions{TRecord}"/>.
/// </summary>
public sealed class RedisHashSetVectorStoreRecordCollectionOptions<TRecord>
{
    /// <summary>
    /// Gets or sets a value indicating whether the collection name should be prefixed to the
    /// key names before reading or writing to the Redis store. Default is true.
    /// </summary>
    /// <remarks>
    /// For a record to be indexed by a specific Redis index, the key name must be prefixed with the matching prefix configured on the Redis index.
    /// You can either pass in keys that are already prefixed, or set this option to true to have the collection name prefixed to the key names automatically.
    /// </remarks>
    public bool PrefixCollectionNameToKeyNames { get; init; } = true;

    /// <summary>
    /// Gets or sets an optional custom mapper to use when converting between the data model and the Redis record.
    /// </summary>
    [Obsolete("Custom mappers are no longer supported.", error: true)]
    public IVectorStoreRecordMapper<TRecord, (string Key, HashEntry[] HashEntries)>? HashEntriesCustomMapper { get; init; } = null;

    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreRecordKeyAttribute"/>, <see cref="VectorStoreRecordDataAttribute"/> and <see cref="VectorStoreRecordVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }
}
