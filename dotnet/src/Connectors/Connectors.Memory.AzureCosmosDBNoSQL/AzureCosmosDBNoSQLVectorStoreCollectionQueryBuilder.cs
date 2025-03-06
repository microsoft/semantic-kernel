﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Contains helpers to build queries for Azure CosmosDB NoSQL.
/// </summary>
internal static class AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder
{
    private const string SelectClauseDelimiter = ",";
    private const string AndConditionDelimiter = " AND ";
    private const string OrConditionDelimiter = " OR ";

    /// <summary>
    /// Builds <see cref="QueryDefinition"/> to get items from Azure CosmosDB NoSQL using vector search.
    /// </summary>
    public static QueryDefinition BuildSearchQuery<TVector, TRecord>(
        TVector vector,
        ICollection<string>? keywords,
        List<string> fields,
        Dictionary<string, string> storagePropertyNames,
        string vectorPropertyName,
        string? textPropertyName,
        string scorePropertyName,
#pragma warning disable CS0618 // Type or member is obsolete
        VectorSearchFilter? oldFilter,
#pragma warning restore CS0618 // Type or member is obsolete
        Expression<Func<TRecord, bool>>? filter,
        int top,
        int skip)
    {
        Verify.NotNull(vector);

        const string VectorVariableName = "@vector";
        // TODO: Use parameterized query for keywords when FullTextScore with parameters is supported.
        //const string KeywordsVariableName = "@keywords";

        var tableVariableName = AzureCosmosDBNoSQLConstants.ContainerAlias;

        var fieldsArgument = fields.Select(field => $"{tableVariableName}.{field}");
        var vectorDistanceArgument = $"VectorDistance({tableVariableName}.{vectorPropertyName}, {VectorVariableName})";
        var vectorDistanceArgumentWithAlias = $"{vectorDistanceArgument} AS {scorePropertyName}";

        // Passing keywords using a parameter is not yet supported for FullTextScore so doing some crude string sanitization in the mean time to frustrate script injection.
        var sanitizedKeywords = keywords is not null ? keywords.Select(x => x.Replace("\"", "")) : null;
        var formattedKeywords = sanitizedKeywords is not null ? $"[\"{string.Join("\", \"", sanitizedKeywords)}\"]" : null;
        var fullTextScoreArgument = textPropertyName is not null && keywords is not null ? $"FullTextScore({tableVariableName}.{textPropertyName}, {formattedKeywords})" : null;

        var rankingArgument = fullTextScoreArgument is null ? vectorDistanceArgument : $"RANK RRF({vectorDistanceArgument}, {fullTextScoreArgument})";

        var selectClauseArguments = string.Join(SelectClauseDelimiter, [.. fieldsArgument, vectorDistanceArgumentWithAlias]);

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        // Build filter object.
        var (whereClause, filterParameters) = (OldFilter: oldFilter, Filter: filter) switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => BuildSearchFilter(legacyFilter, storagePropertyNames),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new AzureCosmosDBNoSqlFilterTranslator().Translate(newFilter, storagePropertyNames),
            _ => (null, [])
        };
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

        var queryParameters = new Dictionary<string, object?>
        {
            [VectorVariableName] = vector
        };

        // If Offset is not configured, use Top parameter instead of Limit/Offset
        // since it's more optimized. Hybrid search doesn't allow top to be passed as a parameter
        // so directly add it to the query here.
        var topArgument = skip == 0 ? $"TOP {top} " : string.Empty;

        var builder = new StringBuilder();

        builder.AppendLine($"SELECT {topArgument}{selectClauseArguments}");
        builder.AppendLine($"FROM {tableVariableName}");

        if (whereClause is not null)
        {
            builder.Append("WHERE ").AppendLine(whereClause);
        }

        builder.AppendLine($"ORDER BY {rankingArgument}");

        if (string.IsNullOrEmpty(topArgument))
        {
            // Hybrid search doesn't allow offset and limit to be passed as parameters
            // so directly add it to the query here.
            builder.AppendLine($"OFFSET {skip} LIMIT {top}");
        }

        // TODO: Use parameterized query for keywords when FullTextScore with parameters is supported.
        //if (fullTextScoreArgument is not null)
        //{
        //    queryParameters.Add(KeywordsVariableName, keywords!.ToArray());
        //}

        var queryDefinition = new QueryDefinition(builder.ToString());

        if (filterParameters is { Count: > 0 })
        {
            queryParameters = queryParameters.Union(filterParameters).ToDictionary(k => k.Key, v => v.Value);
        }

        foreach (var queryParameter in queryParameters)
        {
            queryDefinition.WithParameter(queryParameter.Key, queryParameter.Value);
        }

        return queryDefinition;
    }

    /// <summary>
    /// Builds <see cref="QueryDefinition"/> to get items from Azure CosmosDB NoSQL.
    /// </summary>
    public static QueryDefinition BuildSelectQuery(
        string keyStoragePropertyName,
        string partitionKeyStoragePropertyName,
        List<AzureCosmosDBNoSQLCompositeKey> keys,
        List<string> fields)
    {
        Verify.True(keys.Count > 0, "At least one key should be provided.", nameof(keys));

        const string RecordKeyVariableName = "@rk";
        const string PartitionKeyVariableName = "@pk";

        var tableVariableName = AzureCosmosDBNoSQLConstants.ContainerAlias;

        var selectClauseArguments = string.Join(SelectClauseDelimiter,
            fields.Select(field => $"{tableVariableName}.{field}"));

        var whereClauseArguments = string.Join(OrConditionDelimiter,
            keys.Select((key, index) =>
                $"({tableVariableName}.{keyStoragePropertyName} = {RecordKeyVariableName}{index} {AndConditionDelimiter} " +
                $"{tableVariableName}.{partitionKeyStoragePropertyName} = {PartitionKeyVariableName}{index})"));

        var query = $"""
                     SELECT {selectClauseArguments}
                     FROM {tableVariableName}
                     WHERE {whereClauseArguments}
                     """;

        var queryDefinition = new QueryDefinition(query);

        for (var i = 0; i < keys.Count; i++)
        {
            var recordKey = keys[i].RecordKey;
            var partitionKey = keys[i].PartitionKey;

            Verify.NotNullOrWhiteSpace(recordKey);
            Verify.NotNullOrWhiteSpace(partitionKey);

            queryDefinition.WithParameter($"{RecordKeyVariableName}{i}", recordKey);
            queryDefinition.WithParameter($"{PartitionKeyVariableName}{i}", partitionKey);
        }

        return queryDefinition;
    }

    #region private

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    private static (string WhereClause, Dictionary<string, object?> Parameters) BuildSearchFilter(
        VectorSearchFilter filter,
        Dictionary<string, string> storagePropertyNames)
    {
        const string EqualOperator = "=";
        const string ArrayContainsOperator = "ARRAY_CONTAINS";
        const string ConditionValueVariableName = "@cv";

        var tableVariableName = AzureCosmosDBNoSQLConstants.ContainerAlias;

        var filterClauses = filter.FilterClauses.ToList();

        var whereClauseBuilder = new StringBuilder();
        var queryParameters = new Dictionary<string, object?>();

        for (var i = 0; i < filterClauses.Count; i++)
        {
            if (i > 0)
            {
                whereClauseBuilder.Append(" AND ");
            }
            var filterClause = filterClauses[i];

            string queryParameterName = $"{ConditionValueVariableName}{i}";
            object queryParameterValue;

            if (filterClause is EqualToFilterClause equalToFilterClause)
            {
                var propertyName = GetStoragePropertyName(equalToFilterClause.FieldName, storagePropertyNames);
                whereClauseBuilder.Append($"{tableVariableName}.{propertyName} {EqualOperator} {queryParameterName}");
                queryParameterValue = equalToFilterClause.Value;
            }
            else if (filterClause is AnyTagEqualToFilterClause anyTagEqualToFilterClause)
            {
                var propertyName = GetStoragePropertyName(anyTagEqualToFilterClause.FieldName, storagePropertyNames);
                whereClauseBuilder.Append($"{ArrayContainsOperator}({tableVariableName}.{propertyName}, {queryParameterName})");
                queryParameterValue = anyTagEqualToFilterClause.Value;
            }
            else
            {
                throw new NotSupportedException(
                    $"Unsupported filter clause type '{filterClause.GetType().Name}'. " +
                    $"Supported filter clause types are: {string.Join(", ", [
                        nameof(EqualToFilterClause),
                        nameof(AnyTagEqualToFilterClause)])}");
            }

            queryParameters.Add(queryParameterName, queryParameterValue);
        }

        return (whereClauseBuilder.ToString(), queryParameters);
    }
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

    private static string GetStoragePropertyName(string propertyName, Dictionary<string, string> storagePropertyNames)
    {
        if (!storagePropertyNames.TryGetValue(propertyName, out var storagePropertyName))
        {
            throw new InvalidOperationException($"Property name '{propertyName}' provided as part of the filter clause is not a valid property name.");
        }

        return storagePropertyName;
    }

    #endregion
}
