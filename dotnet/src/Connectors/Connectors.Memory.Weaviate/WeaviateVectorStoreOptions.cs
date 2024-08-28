// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Options when creating a <see cref="WeaviateVectorStore"/>.
/// </summary>
public sealed class WeaviateVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="WeaviateVectorStoreRecordCollection{TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    public IWeaviateVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
