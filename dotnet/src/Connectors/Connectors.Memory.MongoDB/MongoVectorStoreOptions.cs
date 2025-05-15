// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Options when creating a <see cref="MongoVectorStore"/>
/// </summary>
public sealed class MongoVectorStoreOptions
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MongoVectorStoreOptions"/> class.
    /// </summary>
    public MongoVectorStoreOptions()
    {
    }

    internal MongoVectorStoreOptions(MongoVectorStoreOptions? source)
    {
        this.EmbeddingGenerator = source?.EmbeddingGenerator;
    }

    /// <summary>
    /// Gets or sets the default embedding generator to use when generating vectors embeddings with this vector store.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
}
