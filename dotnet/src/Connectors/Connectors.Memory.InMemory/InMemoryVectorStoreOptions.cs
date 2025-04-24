// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Options when creating a <see cref="InMemoryVectorStore"/>.
/// </summary>
public sealed class InMemoryVectorStoreOptions
{
    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }
}
