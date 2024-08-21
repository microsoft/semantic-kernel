// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Options when creating a <see cref="AzureAISearchVectorStore"/>.
/// </summary>
public sealed class AzureAISearchVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    public IAzureAISearchVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }
}
