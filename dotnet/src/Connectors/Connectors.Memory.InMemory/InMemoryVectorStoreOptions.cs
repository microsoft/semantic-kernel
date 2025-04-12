// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Options when creating a <see cref="InMemoryVectorStore"/>.
/// </summary>
public sealed class InMemoryVectorStoreOptions
{
    /// <summary>
    /// An optional name for the store, allowing multiple instances of <see cref="InMemoryVectorStore" /> to share the same
    /// collections within the process. If <see langword="null" />, all collections are private to the instance.
    /// </summary>
    public string? StoreName { get; init; }

    /// <summary>
    /// Gets or sets the embedding generator to use by default for vector properties in this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }
}
