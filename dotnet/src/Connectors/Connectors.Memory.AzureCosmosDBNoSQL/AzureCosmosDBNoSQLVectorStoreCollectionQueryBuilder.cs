// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
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
    public static QueryDefinition BuildSearchQuery<TVector>(
        TVector vector,
        List<string> fields,
        Dictionary<string, string> storagePropertyNames,
        string vectorPropertyName,
        string scorePropertyName,
        VectorSearchOptions searchOptions)
    {
        Verify.NotNull(vector);

        const string VectorVariableName = "@vector";
        const string OffsetVariableName = "@offset";
        const string LimitVariableName = "@limit";
        const string TopVariableName = "@top";

        var tableVariableName = AzureCosmosDBNoSQLConstants.TableQueryVariableName;

        var fieldsArgument = fields.Select(field => $"{tableVariableName}.{field}");
        var vectorDistanceArgument = $"VectorDistance({tableVariableName}.{vectorPropertyName}, {VectorVariableName})";
        var vectorDistanceArgumentWithAlias = $"{vectorDistanceArgument} AS {scorePropertyName}";

        var selectClauseArguments = string.Join(SelectClauseDelimiter, [.. fieldsArgument, vectorDistanceArgumentWithAlias]);

        var filter = BuildSearchFilter(searchOptions.Filter, storagePropertyNames);

        var filterQueryParameters = filter?.QueryParameters;
        var filterWhereClauseArguments = filter?.WhereClauseArguments;
        var queryParameters = new Dictionary<string, object>
        {
            [VectorVariableName] = vector
        };

        var whereClause = filterWhereClauseArguments is { Count: > 0 } ?
            $"WHERE {string.Join(AndConditionDelimiter, filterWhereClauseArguments)}" :
            string.Empty;

        // If Offset is not configured, use Top parameter instead of Limit/Offset
        // since it's more optimized.
        var topArgument = searchOptions.Skip == 0 ? $"TOP {TopVariableName} " : string.Empty;

        var builder = new StringBuilder();

        builder.AppendLine($"SELECT {topArgument}{selectClauseArguments}");
        builder.AppendLine($"FROM {tableVariableName}");

        if (filterWhereClauseArguments is { Count: > 0 })
        {
            builder.AppendLine($"WHERE {string.Join(AndConditionDelimiter, filterWhereClauseArguments)}");
        }

        builder.AppendLine($"ORDER BY {vectorDistanceArgument}");

        if (!string.IsNullOrEmpty(topArgument))
        {
            queryParameters.Add(TopVariableName, searchOptions.Top);
        }
        else
        {
            builder.AppendLine($"OFFSET {OffsetVariableName} LIMIT {LimitVariableName}");
            queryParameters.Add(OffsetVariableName, searchOptions.Skip);
            queryParameters.Add(LimitVariableName, searchOptions.Top);
        }

        var queryDefinition = new QueryDefinition(builder.ToString());

        if (filterQueryParameters is { Count: > 0 })
        {
            queryParameters = queryParameters.Union(filterQueryParameters).ToDictionary(k => k.Key, v => v.Value);
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

        var tableVariableName = AzureCosmosDBNoSQLConstants.TableQueryVariableName;

        var selectClauseArguments = string.Join(SelectClauseDelimiter,
            fields.Select(field => $"{tableVariableName}.{field}"));

        var whereClauseArguments = string.Join(OrConditionDelimiter,
            keys.Select((key, index) =>
                $"({tableVariableName}.{keyStoragePropertyName} = {RecordKeyVariableName}{index} {AndConditionDelimiter} " +
                $"{tableVariableName}.{partitionKeyStoragePropertyName} = {PartitionKeyVariableName}{index})"));

        var query =
            $"SELECT {selectClauseArguments} " +
            $"FROM {tableVariableName} " +
            $"WHERE {whereClauseArguments} ";

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

    private static AzureCosmosDBNoSQLFilter? BuildSearchFilter(
        VectorSearchFilter? filter,
        Dictionary<string, string> storagePropertyNames)
    {
        const string EqualOperator = "=";
        const string ArrayContainsOperator = "ARRAY_CONTAINS";
        const string ConditionValueVariableName = "@cv";

        var tableVariableName = AzureCosmosDBNoSQLConstants.TableQueryVariableName;

        var filterClauses = filter?.FilterClauses.ToList();

        if (filterClauses is not { Count: > 0 })
        {
            return null;
        }

        var whereClauseArguments = new List<string>();
        var queryParameters = new Dictionary<string, object>();

        for (var i = 0; i < filterClauses.Count; i++)
        {
            var filterClause = filterClauses[i];

            string queryParameterName = $"{ConditionValueVariableName}{i}";
            object queryParameterValue;
            string whereClauseArgument;

            if (filterClause is EqualToFilterClause equalToFilterClause)
            {
                var propertyName = GetStoragePropertyName(equalToFilterClause.FieldName, storagePropertyNames);
                whereClauseArgument = $"{tableVariableName}.{propertyName} {EqualOperator} {queryParameterName}";
                queryParameterValue = equalToFilterClause.Value;
            }
            else if (filterClause is AnyTagEqualToFilterClause anyTagEqualToFilterClause)
            {
                var propertyName = GetStoragePropertyName(anyTagEqualToFilterClause.FieldName, storagePropertyNames);
                whereClauseArgument = $"{ArrayContainsOperator}({tableVariableName}.{propertyName}, {queryParameterName})";
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

            whereClauseArguments.Add(whereClauseArgument);
            queryParameters.Add(queryParameterName, queryParameterValue);
        }

        return new AzureCosmosDBNoSQLFilter
        {
            WhereClauseArguments = whereClauseArguments,
            QueryParameters = queryParameters,
        };
    }

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
