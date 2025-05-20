// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Options when creating a <see cref="RedisJsonCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class RedisJsonCollectionOptions : VectorStoreCollectionOptions
{
    internal static readonly RedisJsonCollectionOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisJsonCollectionOptions"/> class.
    /// </summary>
    public RedisJsonCollectionOptions()
    {
    }

    internal RedisJsonCollectionOptions(RedisJsonCollectionOptions? source) : base(source)
    {
        this.PrefixCollectionNameToKeyNames = source?.PrefixCollectionNameToKeyNames ?? Default.PrefixCollectionNameToKeyNames;
        this.JsonSerializerOptions = source?.JsonSerializerOptions;
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

    /// <summary>
    /// Gets or sets the JSON serializer options to use when converting between the data model and the Redis record.
    /// </summary>
    public JsonSerializerOptions? JsonSerializerOptions { get; set; }
}
