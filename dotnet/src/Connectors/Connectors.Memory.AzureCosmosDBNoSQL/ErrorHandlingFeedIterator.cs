// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

internal class ErrorHandlingFeedIterator<T> : FeedIterator<T>
{
    private readonly FeedIterator<T> _internalFeedIterator;
    private readonly string _operationName;
    private readonly VectorStoreRecordCollectionMetadata _collectionMetadata;

    public ErrorHandlingFeedIterator(
        FeedIterator<T> internalFeedIterator,
        VectorStoreRecordCollectionMetadata collectionMetadata,
        string operationName)
    {
        this._internalFeedIterator = internalFeedIterator;
        this._operationName = operationName;
        this._collectionMetadata = collectionMetadata;
    }

    public ErrorHandlingFeedIterator(
        FeedIterator<T> internalFeedIterator,
        VectorStoreMetadata metadata,
        string operationName)
    {
        this._internalFeedIterator = internalFeedIterator;
        this._operationName = operationName;
        this._collectionMetadata = new VectorStoreRecordCollectionMetadata()
        {
            CollectionName = null,
            VectorStoreName = metadata.VectorStoreName,
            VectorStoreSystemName = metadata.VectorStoreSystemName,
        };
    }

    public override bool HasMoreResults => this._internalFeedIterator.HasMoreResults;

    public override Task<FeedResponse<T>> ReadNextAsync(CancellationToken cancellationToken = default)
    {
        return VectorStoreErrorHandler.RunOperationAsync<FeedResponse<T>, CosmosException>(
            this._collectionMetadata,
            this._operationName,
            () => this._internalFeedIterator.ReadNextAsync(cancellationToken));
    }
}
