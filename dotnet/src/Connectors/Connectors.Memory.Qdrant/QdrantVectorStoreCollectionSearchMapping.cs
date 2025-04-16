// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Contains mapping helpers to use when searching for documents using Qdrant.
/// </summary>
internal static class QdrantVectorStoreCollectionSearchMapping
{
#pragma warning disable CS0618 // Type or member is obsolete
    /// <summary>
    /// Build a Qdrant <see cref="Filter"/> from the provided <see cref="VectorSearchFilter"/>.
    /// </summary>
    /// <param name="basicVectorSearchFilter">The <see cref="VectorSearchFilter"/> to build a Qdrant <see cref="Filter"/> from.</param>
    /// <param name="model">The model.</param>
    /// <returns>The Qdrant <see cref="Filter"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown when the provided filter contains unsupported types, values or unknown properties.</exception>
    public static Filter BuildFromLegacyFilter(VectorSearchFilter basicVectorSearchFilter, VectorStoreRecordModel model)
    {
        var filter = new Filter();

        foreach (var filterClause in basicVectorSearchFilter.FilterClauses)
        {
            string fieldName;
            object filterValue;

            // In Qdrant, tag list contains is handled using a keyword match, which is the same as a string equality check.
            // We can therefore just extract the field name and value from each clause and handle them the same.
            if (filterClause is EqualToFilterClause equalityFilterClause)
            {
                fieldName = equalityFilterClause.FieldName;
                filterValue = equalityFilterClause.Value;
            }
            else if (filterClause is AnyTagEqualToFilterClause tagListContainsClause)
            {
                fieldName = tagListContainsClause.FieldName;
                filterValue = tagListContainsClause.Value;
            }
            else
            {
                throw new InvalidOperationException($"Unsupported filter clause type '{filterClause.GetType().Name}'.");
            }

            // Get the storage name for the field.
            if (!model.PropertyMap.TryGetValue(fieldName, out var property))
            {
                throw new InvalidOperationException($"Property name '{fieldName}' provided as part of the filter clause is not a valid property name.");
            }

            // Map DateTimeOffset equality.
            if (filterValue is DateTimeOffset dateTimeOffset)
            {
                var range = new global::Qdrant.Client.Grpc.DatetimeRange
                {
                    Gte = Google.Protobuf.WellKnownTypes.Timestamp.FromDateTimeOffset(dateTimeOffset),
                    Lte = Google.Protobuf.WellKnownTypes.Timestamp.FromDateTimeOffset(dateTimeOffset),
                };

                filter.Must.Add(new Condition() { Field = new FieldCondition() { Key = property.StorageName, DatetimeRange = range } });
                continue;
            }

            // Map each type of filter value to the appropriate Qdrant match type.
            var match = filterValue switch
            {
                string stringValue => new Match { Keyword = stringValue },
                int intValue => new Match { Integer = intValue },
                long longValue => new Match { Integer = longValue },
                bool boolValue => new Match { Boolean = boolValue },
                _ => throw new InvalidOperationException($"Unsupported filter value type '{filterValue.GetType().Name}'.")
            };

            filter.Must.Add(new Condition() { Field = new FieldCondition() { Key = property.StorageName, Match = match } });
        }

        return filter;
    }
#pragma warning restore CS0618 // Type or member is obsolete

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
        QdrantVectorStoreRecordMapper<TRecord> mapper,
        bool includeVectors,
        string vectorStoreSystemName,
        string? vectorStoreName,
        string collectionName,
        string operationName)
    {
        // Do the mapping with error handling.
        return new VectorSearchResult<TRecord>(
            VectorStoreErrorHandler.RunModelConversion(
                vectorStoreSystemName,
                vectorStoreName,
                collectionName,
                operationName,
                () => mapper.MapFromStorageToDataModel(point.Id, point.Payload, point.Vectors, new() { IncludeVectors = includeVectors })),
            point.Score);
    }

    internal static TRecord MapRetrievedPointToRecord<TRecord>(
        RetrievedPoint point,
        QdrantVectorStoreRecordMapper<TRecord> mapper,
        bool includeVectors,
        string vectorStoreSystemName,
        string? vectorStoreName,
        string collectionName,
        string operationName)
    {
        // Do the mapping with error handling.
        return VectorStoreErrorHandler.RunModelConversion(
                vectorStoreSystemName,
                vectorStoreName,
                collectionName,
                operationName,
                () => mapper.MapFromStorageToDataModel(point.Id, point.Payload, point.Vectors, new() { IncludeVectors = includeVectors }));
    }
}
