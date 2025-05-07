// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Options when creating a <see cref="MongoVectorStore"/>
/// </summary>
public sealed class MongoVectorStoreOptions
{
    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
