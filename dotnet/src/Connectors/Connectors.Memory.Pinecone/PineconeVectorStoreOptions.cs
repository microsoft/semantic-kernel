// Copyright (c) Microsoft. All rights reserved.

using System;
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
    public IEmbeddingGenerator? EmbeddingGenerator { get; init; }

    /// <summary>
    /// An optional factory to use for constructing <see cref="PineconeVectorStoreRecordCollection{TKey, TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    [Obsolete("To control how collections are instantiated, extend your provider's IVectorStore implementation and override GetCollection()")]
    public IPineconeVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
