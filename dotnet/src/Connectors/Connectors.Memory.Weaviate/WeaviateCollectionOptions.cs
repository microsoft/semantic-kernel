// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Options when creating a <see cref="WeaviateCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class WeaviateCollectionOptions : VectorStoreCollectionOptions
{
    internal static readonly WeaviateCollectionOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateCollectionOptions"/> class.
    /// </summary>
    public WeaviateCollectionOptions()
    {
    }

    internal WeaviateCollectionOptions(WeaviateCollectionOptions? source) : base(source)
    {
        this.Endpoint = source?.Endpoint;
        this.ApiKey = source?.ApiKey;
        this.HasNamedVectors = source?.HasNamedVectors ?? Default.HasNamedVectors;
    }

    /// <summary>
    /// Weaviate endpoint for remote or local cluster.
    /// </summary>
    public Uri? Endpoint { get; set; }

    /// <summary>
    /// Weaviate API key.
    /// </summary>
    /// <remarks>
    /// This parameter is optional because authentication may be disabled in local clusters for testing purposes.
    /// </remarks>
    public string? ApiKey { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector in Weaviate collection.
    /// Defaults to multiple named vectors.
    /// <see href="https://weaviate.io/developers/weaviate/config-refs/schema/multi-vector"/>.
    /// </summary>
    public bool HasNamedVectors { get; set; } = true;
}
