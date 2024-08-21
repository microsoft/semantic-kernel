// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Options when creating a <see cref="QdrantVectorStore"/>.
/// </summary>
public sealed class QdrantVectorStoreOptions
{
    /// <summary>
    /// Gets or sets a value indicating whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector per qdrant point.
    /// Defaults to single vector per point.
    /// </summary>
    public bool HasNamedVectors { get; set; } = false;

    /// <summary>
    /// An optional factory to use for constructing <see cref="QdrantVectorStoreRecordCollection{TRecord}"/> instances, if custom options are required.
    /// </summary>
    public IQdrantVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
