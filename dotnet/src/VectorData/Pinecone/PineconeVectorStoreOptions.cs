// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Options when creating a <see cref="PineconeVectorStore"/>.
/// </summary>
public sealed class PineconeVectorStoreOptions
{
    /// <summary>
    /// Gets or sets the default embedding generator for vector properties in this collection.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeVectorStoreOptions"/> class.
    /// </summary>
    public PineconeVectorStoreOptions()
    {
    }

    internal PineconeVectorStoreOptions(PineconeVectorStoreOptions? source)
    {
        this.EmbeddingGenerator = source?.EmbeddingGenerator;
    }
}
