﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.Extensions.VectorData;

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
    public static string BuildSearchQuery<TVector>(
        TVector vector,
        string collectionName,
        string vectorPropertyName,
        string keyPropertyName,
        JsonSerializerOptions jsonSerializerOptions,
        VectorSearchOptions searchOptions,
        IReadOnlyDictionary<string, string> storagePropertyNames,
        IReadOnlyList<string> vectorPropertyStorageNames,
        IReadOnlyList<string> dataPropertyStorageNames)
    {
        var vectorsQuery = searchOptions.IncludeVectors ?
            $"vectors {{ {string.Join(" ", vectorPropertyStorageNames)} }}" :
            string.Empty;

        var filter = BuildFilter(
            searchOptions.Filter,
            jsonSerializerOptions,
            keyPropertyName,
            storagePropertyNames);

        var vectorArray = JsonSerializer.Serialize(vector, jsonSerializerOptions);

        return $$"""
        {
          Get {
            {{collectionName}} (
              limit: {{searchOptions.Top}}
              offset: {{searchOptions.Skip}}
              {{filter}}
              nearVector: {
                targetVectors: ["{{vectorPropertyName}}"]
                vector: {{vectorArray}}
              }
            ) {
              {{string.Join(" ", dataPropertyStorageNames)}}
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

    #region private

    /// <summary>
    /// Builds filter for Weaviate search query.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/api/graphql/filters"/>.
    /// </summary>
    private static string BuildFilter(
        VectorSearchFilter? vectorSearchFilter,
        JsonSerializerOptions jsonSerializerOptions,
        string keyPropertyName,
        IReadOnlyDictionary<string, string> storagePropertyNames)
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

            string? storagePropertyName;

            if (propertyName.Equals(keyPropertyName, StringComparison.Ordinal))
            {
                storagePropertyName = WeaviateConstants.ReservedKeyPropertyName;
            }
            else if (!storagePropertyNames.TryGetValue(propertyName, out storagePropertyName))
            {
                throw new InvalidOperationException($"Property name '{propertyName}' provided as part of the filter clause is not a valid property name.");
            }

            var operand = $$"""{ path: ["{{storagePropertyName}}"], operator: {{filterOperator}}, {{filterValueType}}: {{propertyValue}} }""";

            operands.Add(operand);
        }

        return $$"""where: { operator: And, operands: [{{string.Join(", ", operands)}}] }""";
    }

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
