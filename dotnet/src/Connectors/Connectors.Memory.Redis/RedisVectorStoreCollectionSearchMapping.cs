// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.InteropServices;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using NRedisStack.Search;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Contains mapping helpers to use when searching in a redis vector collection.
/// </summary>
internal static class RedisVectorStoreCollectionSearchMapping
{
    /// <summary>
    /// Validate that the given vector is one of the types supported by the Redis connector and convert it to a byte array.
    /// </summary>
    /// <typeparam name="TVector">The vector type.</typeparam>
    /// <param name="vector">The vector to validate and convert.</param>
    /// <param name="connectorTypeName">The type of connector, HashSet or JSON, to use for error reporting.</param>
    /// <returns>The vector converted to a byte array.</returns>
    /// <exception cref="NotSupportedException">Thrown if the vector type is not supported.</exception>
    public static byte[] ValidateVectorAndConvertToBytes<TVector>(TVector vector, string connectorTypeName)
        => vector switch
        {
            ReadOnlyMemory<float> floatVector => MemoryMarshal.AsBytes(floatVector.Span).ToArray(),
            ReadOnlyMemory<double> doubleVector => MemoryMarshal.AsBytes(doubleVector.Span).ToArray(),
            _ => throw new NotSupportedException($"The provided vector type {vector?.GetType().FullName} is not supported by the Redis {connectorTypeName} connector.")
        };

    /// <summary>
    /// Build a Redis <see cref="Query"/> object from the given vector and options.
    /// </summary>
    /// <param name="vectorBytes">The vector to search the database with as a byte array.</param>
    /// <param name="top">The maximum number of elements to return.</param>
    /// <param name="options">The options to configure the behavior of the search.</param>
    /// <param name="model">The model.</param>
    /// <param name="vectorProperty">The vector property.</param>
    /// <param name="selectFields">The set of fields to limit the results to. Null for all.</param>
    /// <returns>The <see cref="Query"/>.</returns>
    public static Query BuildQuery<TRecord>(byte[] vectorBytes, int top, VectorSearchOptions<TRecord> options, VectorStoreRecordModel model, VectorStoreRecordVectorPropertyModel vectorProperty, string[]? selectFields)
    {
        // Build search query.
        var redisLimit = top + options.Skip;

#pragma warning disable CS0618 // Type or member is obsolete
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => BuildLegacyFilter(legacyFilter, model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new RedisFilterTranslator().Translate(newFilter, model),
            _ => "*"
        };
#pragma warning restore CS0618 // Type or member is obsolete

        var query = new Query($"{filter}=>[KNN {redisLimit} @{vectorProperty.StorageName} $embedding AS vector_score]")
            .AddParam("embedding", vectorBytes)
            .SetSortBy("vector_score")
            .Limit(options.Skip, redisLimit)
            .SetWithScores(true)
            .Dialect(2);

        if (selectFields != null)
        {
            query.ReturnFields(selectFields);
        }

        return query;
    }

    internal static Query BuildQuery<TRecord>(Expression<Func<TRecord, bool>> filter, int top, GetFilteredRecordOptions<TRecord> options, VectorStoreRecordModel model)
    {
        var translatedFilter = new RedisFilterTranslator().Translate(filter, model);
        Query query = new Query(translatedFilter)
            .Limit(options.Skip, top)
            .Dialect(2);

        var sortInfo = options.OrderBy.Values.Count switch
        {
            0 => null,
            1 => options.OrderBy.Values[0],
            _ => throw new NotSupportedException("Redis does not support ordering by more than one property.")
        };

        if (sortInfo is not null)
        {
            string storageName = model.GetDataOrKeyProperty(sortInfo.PropertySelector).StorageName;
            query = query.SetSortBy(field: storageName, ascending: sortInfo.Ascending);
        }

        return query;
    }

    /// <summary>
    /// Build a redis filter string from the provided <see cref="VectorSearchFilter"/>.
    /// </summary>
    /// <param name="basicVectorSearchFilter">The <see cref="VectorSearchFilter"/> to build the Redis filter string from.</param>
    /// <param name="model">The model.</param>
    /// <returns>The Redis filter string.</returns>
    /// <exception cref="InvalidOperationException">Thrown when a provided filter value is not supported.</exception>
#pragma warning disable CS0618 // Type or member is obsolete
    public static string BuildLegacyFilter(VectorSearchFilter basicVectorSearchFilter, VectorStoreRecordModel model)
    {
        var filterClauses = basicVectorSearchFilter.FilterClauses.Select(clause =>
        {
            if (clause is EqualToFilterClause equalityFilterClause)
            {
                var storagePropertyName = GetStoragePropertyName(model, equalityFilterClause.FieldName);

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
            else if (clause is AnyTagEqualToFilterClause tagListContainsClause)
            {
                var storagePropertyName = GetStoragePropertyName(model, tagListContainsClause.FieldName);
                return $"@{storagePropertyName}:{{{tagListContainsClause.Value}}}";
            }
            else
            {
                throw new InvalidOperationException($"Unsupported filter clause type '{clause.GetType().Name}'.");
            }
        });

        return $"({string.Join(" ", filterClauses)})";
    }
#pragma warning restore CS0618 // Type or member is obsolete

    /// <summary>
    /// Resolve the distance function to use for a search by checking the distance function of the vector property specified in options
    /// or by falling back to the distance function of the first vector property, or by falling back to the default distance function.
    /// </summary>
    /// <param name="vectorProperty">The vector property to be used.</param>
    /// <returns>The distance function for the vector we want to search.</returns>
    public static string ResolveDistanceFunction(VectorStoreRecordVectorPropertyModel vectorProperty)
        => vectorProperty.DistanceFunction ?? DistanceFunction.CosineSimilarity;

    /// <summary>
    /// Convert the score from redis into the appropriate output score based on the distance function.
    /// Redis doesn't support Cosine Similarity, so we need to convert from distance to similarity if it was chosen.
    /// </summary>
    /// <param name="redisScore">The redis score to convert.</param>
    /// <param name="distanceFunction">The distance function used in the search.</param>
    /// <returns>The converted score.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the provided distance function is not supported by redis.</exception>
    public static float? GetOutputScoreFromRedisScore(float? redisScore, string distanceFunction)
    {
        if (redisScore is null)
        {
            return null;
        }

        return distanceFunction switch
        {
            DistanceFunction.CosineSimilarity => 1 - redisScore,
            DistanceFunction.CosineDistance => redisScore,
            DistanceFunction.DotProductSimilarity => redisScore,
            DistanceFunction.EuclideanSquaredDistance => redisScore,
            _ => throw new InvalidOperationException($"The distance function '{distanceFunction}' is not supported."),
        };
    }

    /// <summary>
    /// Gets the name of the name under which the property with the given name is stored.
    /// </summary>
    /// <param name="model">The model.</param>
    /// <param name="fieldName">The name of the property in the data model.</param>
    /// <returns>The name that the property os stored under.</returns>
    /// <exception cref="InvalidOperationException">Thrown when the property name is not found.</exception>
    private static string GetStoragePropertyName(VectorStoreRecordModel model, string fieldName)
    {
        if (!model.PropertyMap.TryGetValue(fieldName, out var property))
        {
            throw new InvalidOperationException($"Property name '{fieldName}' provided as part of the filter clause is not a valid property name.");
        }

        return property.StorageName;
    }
}
