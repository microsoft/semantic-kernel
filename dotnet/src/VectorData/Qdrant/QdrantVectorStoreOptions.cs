// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Options when creating a <see cref="QdrantVectorStore"/>.
/// </summary>
public sealed class QdrantVectorStoreOptions
{
    internal static readonly QdrantVectorStoreOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStoreOptions"/> class.
    /// </summary>
    public QdrantVectorStoreOptions()
    {
    }

    internal QdrantVectorStoreOptions(QdrantVectorStoreOptions? source)
    {
        this.HasNamedVectors = source?.HasNamedVectors ?? Default.HasNamedVectors;
        this.EmbeddingGenerator = source?.EmbeddingGenerator;
    }

    /// <summary>
    /// Gets or sets a value indicating whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector per qdrant point.
    /// Defaults to single vector per point.
    /// </summary>
    public bool HasNamedVectors { get; set; }

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
