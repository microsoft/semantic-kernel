// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Options when creating a <see cref="MongoDBVectorStore"/>
/// </summary>
public sealed class MongoDBVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="MongoDBVectorStoreRecordCollection{TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    public IMongoDBVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
