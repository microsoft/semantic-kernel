﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Data;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Contains mapping helpers to use when searching for documents using Qdrant.
/// </summary>
internal static class QdrantVectorStoreCollectionSearchMapping
{
    /// <summary>
    /// Build a Qdrant <see cref="Filter"/> from the provided <see cref="VectorSearchFilter"/>.
    /// </summary>
    /// <param name="basicVectorSearchFilter">The <see cref="VectorSearchFilter"/> to build a Qdrant <see cref="Filter"/> from.</param>
    /// <param name="storagePropertyNames">A mapping of data model property names to the names under which they are stored.</param>
    /// <returns>The Qdrant <see cref="Filter"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown when the provided filter contains unsupported types, values or unknown properties.</exception>
    public static Filter BuildFilter(VectorSearchFilter? basicVectorSearchFilter, IReadOnlyDictionary<string, string> storagePropertyNames)
    {
        var filter = new Filter();

        // Return an empty filter if no filter clauses are provided.
        if (basicVectorSearchFilter?.FilterClauses is null)
        {
            return filter;
        }

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

            // Map each type of filter value to the appropriate Qdrant match type.
            var match = filterValue switch
            {
                string stringValue => new Match { Keyword = stringValue },
                int intValue => new Match { Integer = intValue },
                long longValue => new Match { Integer = longValue },
                bool boolValue => new Match { Boolean = boolValue },
                _ => throw new InvalidOperationException($"Unsupported filter value type '{filterValue.GetType().Name}'.")
            };

            // Get the storage name for the field.
            if (!storagePropertyNames.TryGetValue(fieldName, out var storagePropertyName))
            {
                throw new InvalidOperationException($"Property name '{fieldName}' provided as part of the filter clause is not a valid property name.");
            }

            filter.Must.Add(new Condition() { Field = new FieldCondition() { Key = storagePropertyName, Match = match } });
        }

        return filter;
    }

    /// <summary>
    /// Map the given <see cref="ScoredPoint"/> to a <see cref="VectorSearchResult{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record to map to.</typeparam>
    /// <param name="point">The point to map to a <see cref="VectorSearchResult{TRecord}"/>.</param>
    /// <param name="mapper">The mapper to perform the main mapping operation with.</param>
    /// <param name="includeVectors">A value indicating whether to include vectors in the mapped result.</param>
    /// <param name="databaseSystemName">The name of the database system the operation is being run on.</param>
    /// <param name="collectionName">The name of the collection the operation is being run on.</param>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <returns>The mapped <see cref="VectorSearchResult{TRecord}"/>.</returns>
    public static VectorSearchResult<TRecord> MapScoredPointToVectorSearchResult<TRecord>(ScoredPoint point, IVectorStoreRecordMapper<TRecord, PointStruct> mapper, bool includeVectors, string databaseSystemName, string collectionName, string operationName)
        where TRecord : class
    {
        // Since the mapper doesn't know about scored points, we need to convert the scored point to a point struct first.
        var pointStruct = new PointStruct
        {
            Id = point.Id,
            Vectors = point.Vectors,
            Payload = { }
        };

        foreach (KeyValuePair<string, Value> payloadEntry in point.Payload)
        {
            pointStruct.Payload.Add(payloadEntry.Key, payloadEntry.Value);
        }

        // Do the mapping with error handling.
        return new VectorSearchResult<TRecord>(
            VectorStoreErrorHandler.RunModelConversion(
                databaseSystemName,
                collectionName,
                operationName,
                () => mapper.MapFromStorageToDataModel(pointStruct, new() { IncludeVectors = includeVectors })),
            point.Score);
    }
}
