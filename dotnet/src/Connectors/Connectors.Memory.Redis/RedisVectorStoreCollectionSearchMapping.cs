// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using Microsoft.SemanticKernel.Data;
using NRedisStack.Search;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Contains mapping helpers to use when searching in a redis vector collection.
/// </summary>
internal static class RedisVectorStoreCollectionSearchMapping
{
    /// <summary>
    /// Build a Redis <see cref="Query"/> object from the given <see cref="VectorizedSearchQuery{TVector}"/>.
    /// </summary>
    /// <param name="floatVectorQuery">The <see cref="VectorizedSearchQuery{TVector}"/> to build the Redis query from.</param>
    /// <param name="storagePropertyNames">A mapping of data model property names to the names under which they are stored.</param>
    /// <param name="firstVectorPropertyName">The name of the first vector property in the data model.</param>
    /// <param name="selectFields">The set of fields to limit the results to. Null for all.</param>
    /// <returns>The <see cref="Query"/>.</returns>
    public static Query BuildQuery(VectorizedSearchQuery<ReadOnlyMemory<float>> floatVectorQuery, Dictionary<string, string> storagePropertyNames, string firstVectorPropertyName, string[]? selectFields)
    {
        // Resolve options.
        var internalOptions = floatVectorQuery.SearchOptions ?? Data.VectorSearchOptions.Default;
        var vectorPropertyName = ResolveVectorFieldName(internalOptions.VectorFieldName, storagePropertyNames, firstVectorPropertyName);

        // Build search query.
        var filter = RedisVectorStoreCollectionSearchMapping.BuildFilter(internalOptions.BasicVectorSearchFilter, storagePropertyNames);
        var vectorBytes = MemoryMarshal.AsBytes(floatVectorQuery.Vector.Span).ToArray();
        var query = new Query($"{filter}=>[KNN {internalOptions.Limit} @{vectorPropertyName} $embedding AS vector_score]")
            .AddParam("embedding", vectorBytes)
            .SetSortBy("vector_score")
            .Limit(internalOptions.Offset, internalOptions.Limit)
            .SetWithScores(true)
            .Dialect(2);

        if (selectFields != null)
        {
            query.ReturnFields(selectFields);
        }

        return query;
    }

    /// <summary>
    /// Build a redis filter string from the provided <see cref="BasicVectorSearchFilter"/>.
    /// </summary>
    /// <param name="basicVectorSearchFilter">The <see cref="BasicVectorSearchFilter"/> to build the Redis filter string from.</param>
    /// <param name="storagePropertyNames">A mapping of data model property names to the names under which they are stored.</param>
    /// <returns>The Redis filter string.</returns>
    /// <exception cref="InvalidOperationException">Thrown when a provided filter value is not supported.</exception>
    public static string BuildFilter(BasicVectorSearchFilter? basicVectorSearchFilter, Dictionary<string, string> storagePropertyNames)
    {
        if (basicVectorSearchFilter == null)
        {
            return "*";
        }

        var filterClauses = basicVectorSearchFilter.FilterClauses.Select(clause =>
        {
            if (clause is EqualityFilterClause equalityFilterClause)
            {
                var storagePropertyName = GetStoragePropertyName(storagePropertyNames, equalityFilterClause.FieldName);

                return equalityFilterClause.Value switch
                {
                    string stringValue => $"@{storagePropertyName}:{{{stringValue}}}",
                    int intValue => $"@{storagePropertyName}:[{intValue} {intValue}]",
                    long longValue => $"@{storagePropertyName}:[{longValue} {longValue}]",
                    float floatValue => $"@{storagePropertyName}:[{floatValue} {floatValue}]",
                    double doubleValue => $"@{storagePropertyName}:[{doubleValue} {doubleValue}]",
                    _ => throw new InvalidOperationException($"Unsupported filter value type '{equalityFilterClause.Value.GetType().Name}'.")
                };
            }
            else if (clause is TagListContainsFilterClause tagListContainsClause)
            {
                var storagePropertyName = GetStoragePropertyName(storagePropertyNames, tagListContainsClause.FieldName);
                return $"@{storagePropertyName}:{{{tagListContainsClause.Value}}}";
            }
            else
            {
                throw new InvalidOperationException($"Unsupported filter clause type '{clause.GetType().Name}'.");
            }
        });

        return $"({string.Join(" ", filterClauses)})";
    }

    /// <summary>
    /// Resolve the vector field name to use for a search by using the storage name for the field name from options
    /// if available, and falling back to the first vector field name if not.
    /// </summary>
    /// <param name="optionsVectorFieldName">The vector field name provided via options.</param>
    /// <param name="storagePropertyNames">A mapping of data model property names to the names under which they are stored.</param>
    /// <param name="firstVectorPropertyName">The name of the first vector property in the data model.</param>
    /// <returns>The resolved vector field name.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the provided field name is not a valid field name.</exception>
    private static string ResolveVectorFieldName(string? optionsVectorFieldName, Dictionary<string, string> storagePropertyNames, string firstVectorPropertyName)
    {
        string? vectorFieldName;
        if (optionsVectorFieldName is not null)
        {
            if (!storagePropertyNames.TryGetValue(optionsVectorFieldName, out vectorFieldName))
            {
                throw new InvalidOperationException($"The collection does not have a vector field named '{optionsVectorFieldName}'.");
            }
        }
        else
        {
            vectorFieldName = firstVectorPropertyName;
        }

        return vectorFieldName!;
    }

    /// <summary>
    /// Gets the name of the name under which the property with the given name is stored.
    /// </summary>
    /// <param name="storagePropertyNames">A mapping of data model property names to the names under which they are stored.</param>
    /// <param name="fieldName">The name of the property in the data model.</param>
    /// <returns>The name that the property os stored under.</returns>
    /// <exception cref="InvalidOperationException">Thrown when the property name is not found.</exception>
    private static string GetStoragePropertyName(Dictionary<string, string> storagePropertyNames, string fieldName)
    {
        if (!storagePropertyNames.TryGetValue(fieldName, out var storageFieldName))
        {
            throw new InvalidOperationException($"Property name '{fieldName}' provided as part of the filter clause is not a valid property name.");
        }

        return storageFieldName;
    }
}
