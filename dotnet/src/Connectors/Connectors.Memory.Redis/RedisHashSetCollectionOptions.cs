// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Options when creating a <see cref="RedisHashSetCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class RedisHashSetCollectionOptions : VectorStoreCollectionOptions
{
    internal static readonly RedisHashSetCollectionOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisHashSetCollectionOptions"/> class.
    /// </summary>
    public RedisHashSetCollectionOptions()
    {
    }

    internal RedisHashSetCollectionOptions(RedisHashSetCollectionOptions? source) : base(source)
    {
        this.PrefixCollectionNameToKeyNames = source?.PrefixCollectionNameToKeyNames ?? Default.PrefixCollectionNameToKeyNames;
    }

    /// <summary>
    /// Gets or sets a value indicating whether the collection name should be prefixed to the
    /// key names before reading or writing to the Redis store. Default is true.
    /// </summary>
    /// <remarks>
    /// For a record to be indexed by a specific Redis index, the key name must be prefixed with the matching prefix configured on the Redis index.
    /// You can either pass in keys that are already prefixed, or set this option to true to have the collection name prefixed to the key names automatically.
    /// </remarks>
    public bool PrefixCollectionNameToKeyNames { get; set; } = true;
}
