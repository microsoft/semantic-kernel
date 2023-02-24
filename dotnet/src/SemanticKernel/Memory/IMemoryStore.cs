// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory.Storage;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// An interface for storing and retrieving indexed <see cref="IEmbeddingWithMetadata{TEmbedding}"/> objects in a datastore.
/// </summary>
/// <typeparam name="TEmbedding">The data type of the embeddings stored datastore.</typeparam>
public interface IMemoryStore<TEmbedding> : IDataStore<IEmbeddingWithMetadata<TEmbedding>>, IEmbeddingIndex<TEmbedding>
    where TEmbedding : unmanaged
{
}
