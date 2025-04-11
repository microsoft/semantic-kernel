// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Text.Json;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Contains methods to build Weaviate queries.
/// </summary>
internal static class WeaviateVectorStoreRecordCollectionQueryBuilder
{
    /// <summary>
    /// Builds Weaviate search query.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/api/graphql/get"/>.
    /// </summary>
    public static string BuildSearchQuery<TRecord, TVector>(
        TVector vector,
        string collectionName,
        string vectorPropertyName,
        JsonSerializerOptions jsonSerializerOptions,
        int top,
        VectorSearchOptions<TRecord> searchOptions,
        VectorStoreRecordModel model,
        bool hasNamedVectors)
    {
        var vectorsQuery = GetVectorsPropertyQuery(searchOptions.IncludeVectors, hasNamedVectors, model);

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = searchOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => BuildLegacyFilter(legacyFilter, jsonSerializerOptions, model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new WeaviateFilterTranslator().Translate(newFilter, model),
            _ => null
        };
#pragma warning restore CS0618

        var vectorArray = JsonSerializer.Serialize(vector, jsonSerializerOptions);

        return $$"""
        {
          Get {
            {{collectionName}} (
              limit: {{top}}
              offset: {{searchOptions.Skip}}
              {{(filter is null ? "" : "where: " + filter)}}
              nearVector: {
                {{GetTargetVectorsQuery(hasNamedVectors, vectorPropertyName)}}
                vector: {{vectorArray}}
              }
            ) {
              {{string.Join(" ", model.DataProperties.Select(p => p.StorageName))}}
              {{WeaviateConstants.AdditionalPropertiesPropertyName}} {
                {{WeaviateConstants.ReservedKeyPropertyName}}
                {{WeaviateConstants.ScorePropertyName}}
                {{vectorsQuery}}
              }
            }
          }
        }
        """;
    }

    /// <summary>
    /// Builds Weaviate search query.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/api/graphql/get"/>.
    /// </summary>
    public static string BuildQuery<TRecord>(
        Expression<Func<TRecord, bool>> filter,
        int top,
        GetFilteredRecordOptions<TRecord> queryOptions,
        string collectionName,
        VectorStoreRecordModel model,
        bool hasNamedVectors)
    {
        var vectorsQuery = GetVectorsPropertyQuery(queryOptions.IncludeVectors, hasNamedVectors, model);

        var sortPaths = string.Join(",", queryOptions.OrderBy.Values.Select(sortInfo =>
        {
            string sortPath = model.GetDataOrKeyProperty(sortInfo.PropertySelector).StorageName;

            return $$"""{ path: ["{{sortPath}}"], order: {{(sortInfo.Ascending ? "asc" : "desc")}} }""";
        }));

        var translatedFilter = new WeaviateFilterTranslator().Translate(filter, model);

        return $$"""
        {
          Get {
            {{collectionName}} (
              limit: {{top}}
              offset: {{queryOptions.Skip}}
              where: {{translatedFilter}}
              sort: [ {{sortPaths}} ]
            ) {
              {{string.Join(" ", model.DataProperties.Select(p => p.StorageName))}}
              {{WeaviateConstants.AdditionalPropertiesPropertyName}} {
                {{WeaviateConstants.ReservedKeyPropertyName}}
                {{WeaviateConstants.ScorePropertyName}}
                {{vectorsQuery}}
              }
            }
          }
        }
        """;
    }

    /// <summary>
    /// Builds Weaviate hybrid search query.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/api/graphql/get"/>.
    /// </summary>
    public static string BuildHybridSearchQuery<TRecord, TVector>(
        TVector vector,
        int top,
        string keywords,
        string collectionName,
        VectorStoreRecordModel model,
        VectorStoreRecordVectorPropertyModel vectorProperty,
        VectorStoreRecordDataPropertyModel textProperty,
        JsonSerializerOptions jsonSerializerOptions,
        HybridSearchOptions<TRecord> searchOptions,
        bool hasNamedVectors)
    {
        var vectorsQuery = GetVectorsPropertyQuery(searchOptions.IncludeVectors, hasNamedVectors, model);

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var filter = searchOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => BuildLegacyFilter(legacyFilter, jsonSerializerOptions, model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new WeaviateFilterTranslator().Translate(newFilter, model),
            _ => null
        };
#pragma warning restore CS0618

        var vectorArray = JsonSerializer.Serialize(vector, jsonSerializerOptions);

        return $$"""
        {
          Get {
            {{collectionName}} (
              limit: {{top}}
              offset: {{searchOptions.Skip}}
              {{(filter is null ? "" : "where: " + filter)}}
              hybrid: {
                query: "{{keywords}}"
                properties: ["{{textProperty.StorageName}}"]
                {{GetTargetVectorsQuery(hasNamedVectors, vectorProperty.StorageName)}}
                vector: {{vectorArray}}
                fusionType: rankedFusion
              }
            ) {
              {{string.Join(" ", model.DataProperties.Select(p => p.StorageName))}}
              {{WeaviateConstants.AdditionalPropertiesPropertyName}} {
                {{WeaviateConstants.ReservedKeyPropertyName}}
                {{WeaviateConstants.HybridScorePropertyName}}
                {{vectorsQuery}}
              }
            }
          }
        }
        """;
    }

    #region private

    private static string GetTargetVectorsQuery(bool hasNamedVectors, string vectorPropertyName)
    {
        return hasNamedVectors ? $"targetVectors: [\"{vectorPropertyName}\"]" : string.Empty;
    }

    private static string GetVectorsPropertyQuery(
        bool includeVectors,
        bool hasNamedVectors,
        VectorStoreRecordModel model)
    {
        return includeVectors
            ? hasNamedVectors
                ? $"vectors {{ {string.Join(" ", model.VectorProperties.Select(p => p.StorageName))} }}"
                : WeaviateConstants.ReservedSingleVectorPropertyName
            : string.Empty;
    }

#pragma warning disable CS0618 // Type or member is obsolete
    /// <summary>
    /// Builds filter for Weaviate search query.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/api/graphql/filters"/>.
    /// </summary>
    private static string BuildLegacyFilter(
        VectorSearchFilter? vectorSearchFilter,
        JsonSerializerOptions jsonSerializerOptions,
        VectorStoreRecordModel model)
    {
        const string EqualOperator = "Equal";
        const string ContainsAnyOperator = "ContainsAny";

        var filterClauses = vectorSearchFilter?.FilterClauses.ToList();

        if (filterClauses is not { Count: > 0 })
        {
            return string.Empty;
        }

        var operands = new List<string>();

        foreach (var filterClause in filterClauses)
        {
            string filterValueType;
            string propertyName;
            object propertyValue;
            string filterOperator;

            if (filterClause is EqualToFilterClause equalToFilterClause)
            {
                filterValueType = GetFilterValueType(equalToFilterClause.Value.GetType());
                propertyName = equalToFilterClause.FieldName;
                propertyValue = JsonSerializer.Serialize(equalToFilterClause.Value, jsonSerializerOptions);
                filterOperator = EqualOperator;
            }
            else if (filterClause is AnyTagEqualToFilterClause anyTagEqualToFilterClause)
            {
                filterValueType = GetFilterValueType(anyTagEqualToFilterClause.Value.GetType());
                propertyName = anyTagEqualToFilterClause.FieldName;
                propertyValue = JsonSerializer.Serialize(new string[] { anyTagEqualToFilterClause.Value }, jsonSerializerOptions);
                filterOperator = ContainsAnyOperator;
            }
            else
            {
                throw new NotSupportedException(
                    $"Unsupported filter clause type '{filterClause.GetType().Name}'. " +
                    $"Supported filter clause types are: {string.Join(", ", [
                        nameof(EqualToFilterClause),
                        nameof(AnyTagEqualToFilterClause)])}");
            }

            if (!model.PropertyMap.TryGetValue(propertyName, out var property))
            {
                throw new InvalidOperationException($"Property name '{propertyName}' provided as part of the filter clause is not a valid property name.");
            }

            var operand = $$"""{ path: ["{{property.StorageName}}"], operator: {{filterOperator}}, {{filterValueType}}: {{propertyValue}} }""";

            operands.Add(operand);
        }

        return $$"""{ operator: And, operands: [{{string.Join(", ", operands)}}] }""";
    }
#pragma warning restore CS0618 // Type or member is obsolete

    /// <summary>
    /// Gets filter value type.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/api/graphql/filters#filter-structure"/>.
    /// </summary>
    private static string GetFilterValueType(Type valueType)
    {
        return valueType switch
        {
            Type t when t == typeof(int) || t == typeof(long) || t == typeof(short) || t == typeof(byte) ||
                        t == typeof(int?) || t == typeof(long?) || t == typeof(short?) || t == typeof(byte?) => "valueInt",
            Type t when t == typeof(bool) || t == typeof(bool?) => "valueBoolean",
            Type t when t == typeof(string) || t == typeof(Guid) || t == typeof(Guid?) => "valueText",
            Type t when t == typeof(float) || t == typeof(double) || t == typeof(decimal) ||
                        t == typeof(float?) || t == typeof(double?) || t == typeof(decimal?) => "valueNumber",
            Type t when t == typeof(DateTimeOffset) || t == typeof(DateTimeOffset?) => "valueDate",
            _ => throw new NotSupportedException($"Unsupported value type {valueType.FullName} in filter.")
        };
    }

    #endregion
}
