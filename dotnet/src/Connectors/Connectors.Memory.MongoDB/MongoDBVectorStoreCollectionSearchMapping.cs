// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Contains mapping helpers to use when searching for documents using MongoDB.
/// </summary>
internal static class MongoDBVectorStoreCollectionSearchMapping
{
    /// <summary>Returns distance function specified on vector property or default <see cref="MongoDBConstants.DefaultDistanceFunction"/>.</summary>
    public static string GetVectorPropertyDistanceFunction(string? distanceFunction) => !string.IsNullOrWhiteSpace(distanceFunction) ? distanceFunction! : MongoDBConstants.DefaultDistanceFunction;

    /// <summary>
    /// Build MongoDB filter from the provided <see cref="VectorSearchFilter"/>.
    /// </summary>
    /// <param name="vectorSearchFilter">The <see cref="VectorSearchFilter"/> to build MongoDB filter from.</param>
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the storage name.</param>
    /// <exception cref="NotSupportedException">Thrown when the provided filter type is unsupported.</exception>
    /// <exception cref="InvalidOperationException">Thrown when property name specified in filter doesn't exist.</exception>
    public static BsonDocument? BuildFilter(
        VectorSearchFilter? vectorSearchFilter,
        Dictionary<string, string> storagePropertyNames)
    {
        const string EqualOperator = "$eq";

        var filterClauses = vectorSearchFilter?.FilterClauses.ToList();

        if (filterClauses is not { Count: > 0 })
        {
            return null;
        }

        var filter = new BsonDocument();

        foreach (var filterClause in filterClauses)
        {
            string propertyName;
            BsonValue propertyValue;
            string filterOperator;

            if (filterClause is EqualToFilterClause equalToFilterClause)
            {
                propertyName = equalToFilterClause.FieldName;
                propertyValue = BsonValue.Create(equalToFilterClause.Value);
                filterOperator = EqualOperator;
            }
            else
            {
                throw new NotSupportedException(
                    $"Unsupported filter clause type '{filterClause.GetType().Name}'. " +
                    $"Supported filter clause types are: {string.Join(", ", [
                        nameof(EqualToFilterClause)])}");
            }

            if (!storagePropertyNames.TryGetValue(propertyName, out var storagePropertyName))
            {
                throw new InvalidOperationException($"Property name '{propertyName}' provided as part of the filter clause is not a valid property name.");
            }

            if (filter.Contains(storagePropertyName))
            {
                if (filter[storagePropertyName] is BsonDocument document && document.Contains(filterOperator))
                {
                    throw new NotSupportedException(
                        $"Filter with operator '{filterOperator}' is already added to '{propertyName}' property. " +
                        "Multiple filters of the same type in the same property are not supported.");
                }

                filter[storagePropertyName][filterOperator] = propertyValue;
            }
            else
            {
                filter[storagePropertyName] = new BsonDocument() { [filterOperator] = propertyValue };
            }
        }

        return filter;
    }

    /// <summary>Returns search part of the search query.</summary>
    public static BsonDocument GetSearchQuery<TVector>(
        TVector vector,
        string indexName,
        string vectorPropertyName,
        int limit,
        int numCandidates,
        BsonDocument? filter)
    {
        var searchQuery = new BsonDocument
        {
            { "index", indexName },
            { "queryVector", BsonArray.Create(vector) },
            { "path", vectorPropertyName },
            { "limit", limit },
            { "numCandidates", numCandidates },
        };

        if (filter is not null)
        {
            searchQuery["filter"] = filter;
        }

        return new BsonDocument
        {
            { "$vectorSearch", searchQuery }
        };
    }

    /// <summary>Returns projection part of the search query to return similarity score together with document.</summary>
    public static BsonDocument GetProjectionQuery(string scorePropertyName, string documentPropertyName)
    {
        return new BsonDocument
        {
            { "$project",
                new BsonDocument
                {
                    { scorePropertyName, new BsonDocument { { "$meta", "vectorSearchScore" } } },
                    { documentPropertyName, "$$ROOT" }
                }
            }
        };
    }
}
