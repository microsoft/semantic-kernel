// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Contains mapping helpers to use when searching for documents using Qdrant.
/// </summary>
internal static class QdrantCollectionSearchMapping
{
    /// <summary>
    /// Map the given <see cref="ScoredPoint"/> to a <see cref="VectorSearchResult{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record to map to.</typeparam>
    /// <param name="point">The point to map to a <see cref="VectorSearchResult{TRecord}"/>.</param>
    /// <param name="mapper">The mapper to perform the main mapping operation with.</param>
    /// <param name="includeVectors">A value indicating whether to include vectors in the mapped result.</param>
    /// <param name="vectorStoreSystemName">The name of the vector store system the operation is being run on.</param>
    /// <param name="vectorStoreName">The name of the vector store the operation is being run on.</param>
    /// <param name="collectionName">The name of the collection the operation is being run on.</param>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <returns>The mapped <see cref="VectorSearchResult{TRecord}"/>.</returns>
    public static VectorSearchResult<TRecord> MapScoredPointToVectorSearchResult<TRecord>(
        ScoredPoint point,
        QdrantMapper<TRecord> mapper,
        bool includeVectors,
        string vectorStoreSystemName,
        string? vectorStoreName,
        string collectionName,
        string operationName)
        where TRecord : class
    {
        // Do the mapping with error handling.
        return new VectorSearchResult<TRecord>(
            mapper.MapFromStorageToDataModel(point.Id, point.Payload, point.Vectors, includeVectors),
            point.Score);
    }

    internal static TRecord MapRetrievedPointToRecord<TRecord>(
        RetrievedPoint point,
        QdrantMapper<TRecord> mapper,
        bool includeVectors,
        string vectorStoreSystemName,
        string? vectorStoreName,
        string collectionName,
        string operationName)
        where TRecord : class
    {
        // Do the mapping with error handling.
        return mapper.MapFromStorageToDataModel(point.Id, point.Payload, point.Vectors, includeVectors);
    }
}
