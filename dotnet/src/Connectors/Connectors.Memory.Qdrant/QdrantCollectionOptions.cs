// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Options when creating a <see cref="QdrantCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class QdrantCollectionOptions : VectorStoreCollectionOptions
{
    internal static readonly QdrantCollectionOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantCollectionOptions"/> class.
    /// </summary>
    public QdrantCollectionOptions()
    {
    }

    internal QdrantCollectionOptions(QdrantCollectionOptions? source) : base(source)
    {
        this.HasNamedVectors = source?.HasNamedVectors ?? Default.HasNamedVectors;
    }

    /// <summary>
    /// Gets or sets a value indicating whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector per qdrant point.
    /// Defaults to single vector per point.
    /// </summary>
    public bool HasNamedVectors { get; set; }
}
