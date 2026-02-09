// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

/// <summary>
/// Contains helpers to build queries for Azure CosmosDB NoSQL.
/// </summary>
internal static class CosmosNoSqlCollectionQueryBuilder
{
    private const string SelectClauseDelimiter = ",";
    private const string AndConditionDelimiter = " AND ";
    private const string OrConditionDelimiter = " OR ";

    /// <summary>
    /// Builds <see cref="QueryDefinition"/> to get items from Azure CosmosDB NoSQL using vector search.
    /// </summary>
    public static QueryDefinition BuildSearchQuery<TRecord>(
        object vector,
        ICollection<string>? keywords,
        CollectionModel model,
        string vectorPropertyName,
        string? distanceFunction,
        string? textPropertyName,
        string scorePropertyName,
#pragma warning disable CS0618 // Type or member is obsolete
        VectorSearchFilter? oldFilter,
#pragma warning restore CS0618 // Type or member is obsolete
        Expression<Func<TRecord, bool>>? filter,
        double? scoreThreshold,
        int top,
        int skip,
        bool includeVectors)
    {
        Verify.NotNull(vector);

        const string VectorVariableName = "@vector";
        // TODO: Use parameterized query for keywords when FullTextScore with parameters is supported.
        //const string KeywordsVariableName = "@keywords";

        var tableVariableName = CosmosNoSqlConstants.ContainerAlias;

        IEnumerable<PropertyModel> projectionProperties = model.Properties;
        if (!includeVectors)
        {
            projectionProperties = projectionProperties.Where(p => p is not VectorPropertyModel);
        }
        var fieldsArgument = projectionProperties.Select(p => GeneratePropertyAccess(tableVariableName, p.StorageName));
        var vectorDistanceArgument = $"VectorDistance({GeneratePropertyAccess(tableVariableName, vectorPropertyName)}, {VectorVariableName})";
        var vectorDistanceArgumentWithAlias = $"{vectorDistanceArgument} AS {scorePropertyName}";

        // Passing keywords using a parameter is not yet supported for FullTextScore so doing some crude string sanitization in the mean time to frustrate script injection.
        var sanitizedKeywords = keywords is not null ? keywords.Select(x => x.Replace("\"", "")) : null;
        var formattedKeywords = sanitizedKeywords is not null ? $"\"{string.Join("\", \"", sanitizedKeywords)}\"" : null;
        var fullTextScoreArgument = textPropertyName is not null && keywords is not null
            ? $"FullTextScore({GeneratePropertyAccess(tableVariableName, textPropertyName)}, {formattedKeywords})"
            : null;

        var rankingArgument = fullTextScoreArgument is null ? vectorDistanceArgument : $"RANK RRF({vectorDistanceArgument}, {fullTextScoreArgument})";

        var selectClauseArguments = string.Join(SelectClauseDelimiter, [.. fieldsArgument, vectorDistanceArgumentWithAlias]);

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        // Build filter object.
        var (filterClause, filterParameters) = (OldFilter: oldFilter, Filter: filter) switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => BuildSearchFilter(legacyFilter, model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new CosmosNoSqlFilterTranslator().Translate(newFilter, model),
            _ => (null, [])
        };
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

        var queryParameters = new Dictionary<string, object?>
        {
            [VectorVariableName] = vector
        };

        // Add score threshold filter if specified.
        // For similarity functions (CosineSimilarity, DotProductSimilarity), higher scores are better, so filter with >=.
        // For distance functions (EuclideanDistance), lower scores are better, so filter with <=.
        const string ScoreThresholdVariableName = "@scoreThreshold";
        string? scoreThresholdClause = null;
        if (scoreThreshold.HasValue)
        {
            var comparisonOperator = distanceFunction switch
            {
                Microsoft.Extensions.VectorData.DistanceFunction.CosineSimilarity => ">=",
                Microsoft.Extensions.VectorData.DistanceFunction.DotProductSimilarity => ">=",
                Microsoft.Extensions.VectorData.DistanceFunction.EuclideanDistance => "<=",
                _ => throw new NotSupportedException($"Score threshold is not supported for distance function '{distanceFunction}'.")
            };
            scoreThresholdClause = $"{vectorDistanceArgument} {comparisonOperator} {ScoreThresholdVariableName}";
            queryParameters[ScoreThresholdVariableName] = scoreThreshold.Value;
        }

        // If Offset is not configured, use Top parameter instead of Limit/Offset
        // since it's more optimized. Hybrid search doesn't allow top to be passed as a parameter
        // so directly add it to the query here.
        var topArgument = skip == 0 ? $"TOP {top} " : string.Empty;

        var builder = new StringBuilder();

        builder.AppendLine($"SELECT {topArgument}{selectClauseArguments}");
        builder.AppendLine($"FROM {tableVariableName}");

        if (filterClause is not null || scoreThresholdClause is not null)
        {
            builder.Append("WHERE ");

            if (filterClause is not null)
            {
                builder.Append(filterClause);
                if (scoreThresholdClause is not null)
                {
                    builder.Append(AndConditionDelimiter);
                }
            }

            if (scoreThresholdClause is not null)
            {
                builder.Append(scoreThresholdClause);
            }

            builder.AppendLine();
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

    internal static QueryDefinition BuildSearchQuery<TRecord>(
        CollectionModel model,
        string whereClause, Dictionary<string, object?> filterParameters,
        FilteredRecordRetrievalOptions<TRecord> filterOptions,
        int top)
    {
        var tableVariableName = CosmosNoSqlConstants.ContainerAlias;

        IEnumerable<PropertyModel> projectionProperties = model.Properties;
        if (!filterOptions.IncludeVectors)
        {
            projectionProperties = projectionProperties.Where(p => p is not VectorPropertyModel);
        }

        var fieldsArgument = projectionProperties.Select(field => GeneratePropertyAccess(tableVariableName, field.StorageName));

        var selectClauseArguments = string.Join(SelectClauseDelimiter, [.. fieldsArgument]);

        // If Offset is not configured, use Top parameter instead of Limit/Offset
        // since it's more optimized.
        var topArgument = filterOptions.Skip == 0 ? $"TOP {top} " : string.Empty;

        var builder = new StringBuilder();

        builder.AppendLine($"SELECT {topArgument}{selectClauseArguments}");
        builder.AppendLine($"FROM {tableVariableName}");
        builder.Append("WHERE ").AppendLine(whereClause);

        var orderBy = filterOptions.OrderBy?.Invoke(new()).Values;
        if (orderBy is { Count: > 0 })
        {
            builder.Append("ORDER BY ");

            foreach (var sortInfo in orderBy)
            {
                builder
                    .Append(GeneratePropertyAccess(tableVariableName, model.GetDataOrKeyProperty(sortInfo.PropertySelector).StorageName))
                    .Append(sortInfo.Ascending ? " ASC," : " DESC,");
            }

            builder.Length--; // remove the last comma
            builder.AppendLine();
        }

        if (string.IsNullOrEmpty(topArgument))
        {
            builder.AppendLine($"OFFSET {filterOptions.Skip} LIMIT {top}");
        }

        var queryDefinition = new QueryDefinition(builder.ToString());

        foreach (var queryParameter in filterParameters)
        {
            queryDefinition.WithParameter(queryParameter.Key, queryParameter.Value);
        }

        return queryDefinition;
    }

    /// <summary>
    /// Builds <see cref="QueryDefinition"/> to get items from Azure CosmosDB NoSQL.
    /// </summary>
    public static QueryDefinition BuildSelectQuery(
        CollectionModel model,
        string keyStoragePropertyName,
        string partitionKeyStoragePropertyName,
        List<CosmosNoSqlCompositeKey> keys,
        bool includeVectors)
    {
        Verify.True(keys.Count > 0, "At least one key should be provided.", nameof(keys));

        const string RecordKeyVariableName = "@rk";
        const string PartitionKeyVariableName = "@pk";

        var tableVariableName = CosmosNoSqlConstants.ContainerAlias;

        IEnumerable<PropertyModel> projectionProperties = model.Properties;
        if (!includeVectors)
        {
            projectionProperties = projectionProperties.Where(p => p is not VectorPropertyModel);
        }

        var selectClauseArguments = string.Join(SelectClauseDelimiter,
            projectionProperties.Select(field => GeneratePropertyAccess(tableVariableName, field.StorageName)));

        var whereClauseArguments = string.Join(OrConditionDelimiter,
            keys.Select((key, index) =>
                $"({GeneratePropertyAccess(tableVariableName, keyStoragePropertyName)} = {RecordKeyVariableName}{index} {AndConditionDelimiter} " +
                $"{GeneratePropertyAccess(tableVariableName, partitionKeyStoragePropertyName)} = {PartitionKeyVariableName}{index})"));

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
        CollectionModel model)
    {
        const string ArrayContainsOperator = "ARRAY_CONTAINS";
        const string ConditionValueVariableName = "@cv";

        var tableVariableName = CosmosNoSqlConstants.ContainerAlias;

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
                var propertyName = GetStoragePropertyName(equalToFilterClause.FieldName, model);
                whereClauseBuilder
                    .Append(GeneratePropertyAccess(tableVariableName, propertyName))
                    .Append(" = ")
                    .Append(queryParameterName);
                queryParameterValue = equalToFilterClause.Value;
            }
            else if (filterClause is AnyTagEqualToFilterClause anyTagEqualToFilterClause)
            {
                var propertyName = GetStoragePropertyName(anyTagEqualToFilterClause.FieldName, model);
                whereClauseBuilder.Append(ArrayContainsOperator)
                    .Append('(')
                    .Append(GeneratePropertyAccess(tableVariableName, propertyName))
                    .Append(", ")
                    .Append(queryParameterName)
                    .Append(')');
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

    private static string GetStoragePropertyName(string propertyName, CollectionModel model)
    {
        if (!model.PropertyMap.TryGetValue(propertyName, out var property))
        {
            throw new InvalidOperationException($"Property name '{propertyName}' provided as part of the filter clause is not a valid property name.");
        }

        return property.StorageName;
    }

    /// <summary>
    /// Escapes a JSON property name for use in Cosmos NoSQL SQL queries.
    /// JSON property names within bracket notation need backslash and double-quote escaping.
    /// </summary>
    private static string EscapeJsonPropertyName(string propertyName)
        => propertyName.Replace(@"\", @"\\").Replace("\"", "\\\"");

    /// <summary>
    /// Generates a property access expression using bracket notation with proper escaping.
    /// </summary>
    private static string GeneratePropertyAccess(char alias, string propertyName)
        => $"{alias}[\"{EscapeJsonPropertyName(propertyName)}\"]";

    #endregion
}
