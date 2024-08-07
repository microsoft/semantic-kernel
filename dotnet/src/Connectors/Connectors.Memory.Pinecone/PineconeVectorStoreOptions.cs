// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Options when creating a <see cref="PineconeVectorStore"/>.
/// </summary>
public sealed class PineconeVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="PineconeVectorStoreRecordCollection{TRecord}"/> instances, if custom options are required.
    /// </summary>
    public IPineconeVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
