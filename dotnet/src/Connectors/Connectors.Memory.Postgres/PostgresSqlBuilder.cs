// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Npgsql;
using NpgsqlTypes;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Provides methods to build SQL commands for managing vector store collections in PostgreSQL.
/// </summary>
internal static class PostgresSqlBuilder
{
    /// <inheritdoc />
    internal static PostgresSqlCommandInfo BuildDoesTableExistCommand(string schema, string tableName)
    {
        return new PostgresSqlCommandInfo(
            commandText: """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = $1
    AND table_type = 'BASE TABLE'
    AND table_name = $2
""",
            parameters: [
                new NpgsqlParameter() { Value = schema },
                new NpgsqlParameter() { Value = tableName }
            ]
        );
    }

    /// <inheritdoc />
    internal static PostgresSqlCommandInfo BuildGetTablesCommand(string schema)
    {
        return new PostgresSqlCommandInfo(
            commandText: """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = $1 AND table_type = 'BASE TABLE'
""",
            parameters: [new NpgsqlParameter() { Value = schema }]
        );
    }

    /// <inheritdoc />
    internal static PostgresSqlCommandInfo BuildCreateTableCommand(string schema, string tableName, VectorStoreRecordModel model, bool ifNotExists = true)
    {
        if (string.IsNullOrWhiteSpace(tableName))
        {
            throw new ArgumentException("Table name cannot be null or whitespace", nameof(tableName));
        }

        var keyName = model.KeyProperty.StorageName;

        StringBuilder createTableCommand = new();
        createTableCommand.AppendLine($"CREATE TABLE {(ifNotExists ? "IF NOT EXISTS " : "")}{schema}.\"{tableName}\" (");

        // Add the key column
        var keyPgTypeInfo = PostgresVectorStoreRecordPropertyMapping.GetPostgresTypeName(model.KeyProperty.Type);
        createTableCommand.AppendLine($"    \"{keyName}\" {keyPgTypeInfo.PgType} {(keyPgTypeInfo.IsNullable ? "" : "NOT NULL")},");

        // Add the data columns
        foreach (var dataProperty in model.DataProperties)
        {
            string columnName = dataProperty.StorageName;
            var dataPgTypeInfo = PostgresVectorStoreRecordPropertyMapping.GetPostgresTypeName(dataProperty.Type);
            createTableCommand.AppendLine($"    \"{columnName}\" {dataPgTypeInfo.PgType} {(dataPgTypeInfo.IsNullable ? "" : "NOT NULL")},");
        }

        // Add the vector columns
        foreach (var vectorProperty in model.VectorProperties)
        {
            string columnName = vectorProperty.StorageName;
            var vectorPgTypeInfo = PostgresVectorStoreRecordPropertyMapping.GetPgVectorTypeName(vectorProperty);
            createTableCommand.AppendLine($"    \"{columnName}\" {vectorPgTypeInfo.PgType} {(vectorPgTypeInfo.IsNullable ? "" : "NOT NULL")},");
        }

        createTableCommand.AppendLine($"    PRIMARY KEY (\"{keyName}\")");

        createTableCommand.AppendLine(");");

        return new PostgresSqlCommandInfo(commandText: createTableCommand.ToString());
    }

    /// <inheritdoc />
    internal static PostgresSqlCommandInfo BuildCreateIndexCommand(string schema, string tableName, string columnName, string indexKind, string distanceFunction, bool isVector, bool ifNotExists)
    {
        var indexName = $"{tableName}_{columnName}_index";

        if (!isVector)
        {
            return new PostgresSqlCommandInfo(commandText:
                $@"CREATE INDEX {(ifNotExists ? "IF NOT EXISTS " : "")}""{indexName}"" ON {schema}.""{tableName}"" (""{columnName}"");"
            );
        }

        // Only support creating HNSW index creation through the connector.
        var indexTypeName = indexKind switch
        {
            IndexKind.Hnsw => "hnsw",
            _ => throw new NotSupportedException($"Index kind '{indexKind}' is not supported for table creation. If you need to create an index of this type, please do so manually. Only HNSW indexes are supported through the vector store.")
        };

        distanceFunction ??= PostgresConstants.DefaultDistanceFunction;  // Default to Cosine distance

        var indexOps = distanceFunction switch
        {
            DistanceFunction.CosineDistance => "vector_cosine_ops",
            DistanceFunction.CosineSimilarity => "vector_cosine_ops",
            DistanceFunction.DotProductSimilarity => "vector_ip_ops",
            DistanceFunction.EuclideanDistance => "vector_l2_ops",
            DistanceFunction.ManhattanDistance => "vector_l1_ops",
            _ => throw new NotSupportedException($"Distance function {distanceFunction} is not supported.")
        };

        return new PostgresSqlCommandInfo(
            commandText: $@"
                CREATE INDEX {(ifNotExists ? "IF NOT EXISTS " : "")} ""{indexName}"" ON {schema}.""{tableName}"" USING {indexTypeName} (""{columnName}"" {indexOps});"
        );
    }

    /// <inheritdoc />
    internal static PostgresSqlCommandInfo BuildDropTableCommand(string schema, string tableName)
    {
        return new PostgresSqlCommandInfo(
            commandText: $@"DROP TABLE IF EXISTS {schema}.""{tableName}"""
        );
    }

    /// <inheritdoc/>
    internal static PostgresSqlCommandInfo BuildUpsertCommand(string schema, string tableName, string keyColumn, Dictionary<string, object?> row)
    {
        var columns = row.Keys.ToList();
        var columnNames = string.Join(", ", columns.Select(k => $"\"{k}\""));
        var valuesParams = string.Join(", ", columns.Select((k, i) => $"${i + 1}"));
        var columnsWithIndex = columns.Select((k, i) => (col: k, idx: i));
        var updateColumnsWithParams = string.Join(", ", columnsWithIndex.Where(c => c.col != keyColumn).Select(c => $"\"{c.col}\"=${c.idx + 1}"));
        var commandText = $"""
INSERT INTO {schema}."{tableName}" ({columnNames})
VALUES ({valuesParams})
ON CONFLICT ("{keyColumn}")
DO UPDATE SET {updateColumnsWithParams};
""";

        return new PostgresSqlCommandInfo(commandText)
        {
            Parameters = columns.Select(c =>
                PostgresVectorStoreRecordPropertyMapping.GetNpgsqlParameter(row[c])
            ).ToList()
        };
    }

    /// <inheritdoc />
    internal static PostgresSqlCommandInfo BuildUpsertBatchCommand(string schema, string tableName, string keyColumn, List<Dictionary<string, object?>> rows)
    {
        if (rows == null || rows.Count == 0)
        {
            throw new ArgumentException("Rows cannot be null or empty", nameof(rows));
        }

        var firstRow = rows[0];
        var columns = firstRow.Keys.ToList();

        // Generate column names and parameter placeholders
        var columnNames = string.Join(", ", columns.Select(c => $"\"{c}\""));
        var valuePlaceholders = string.Join(", ", columns.Select((c, i) => $"${i + 1}"));
        var valuesRows = string.Join(", ",
            rows.Select((row, rowIndex) =>
                $"({string.Join(", ",
                    columns.Select((c, colIndex) => $"${rowIndex * columns.Count + colIndex + 1}"))})"));

        // Generate the update set clause
        var updateSetClause = string.Join(", ", columns.Where(c => c != keyColumn).Select(c => $"\"{c}\" = EXCLUDED.\"{c}\""));

        // Generate the SQL command
        var commandText = $"""
INSERT INTO {schema}."{tableName}" ({columnNames})
VALUES {valuesRows}
ON CONFLICT ("{keyColumn}")
DO UPDATE SET {updateSetClause};
""";

        // Generate the parameters
        var parameters = new List<NpgsqlParameter>();
        for (int rowIndex = 0; rowIndex < rows.Count; rowIndex++)
        {
            var row = rows[rowIndex];
            foreach (var column in columns)
            {
                parameters.Add(new NpgsqlParameter()
                {
                    Value = row[column] ?? DBNull.Value
                });
            }
        }

        return new PostgresSqlCommandInfo(commandText, parameters);
    }

    /// <inheritdoc />
    internal static PostgresSqlCommandInfo BuildGetCommand<TKey>(string schema, string tableName, VectorStoreRecordModel model, TKey key, bool includeVectors = false)
        where TKey : notnull
    {
        List<string> queryColumns = new();

        foreach (var property in model.Properties)
        {
            queryColumns.Add($"\"{property.StorageName}\"");
        }

        var queryColumnList = string.Join(", ", queryColumns);

        return new PostgresSqlCommandInfo(
            commandText: $"""
SELECT {queryColumnList}
FROM {schema}."{tableName}"
WHERE "{model.KeyProperty.StorageName}" = ${1};
""",
            parameters: [new NpgsqlParameter() { Value = key }]
        );
    }

    /// <inheritdoc />
    internal static PostgresSqlCommandInfo BuildGetBatchCommand<TKey>(string schema, string tableName, VectorStoreRecordModel model, List<TKey> keys, bool includeVectors = false)
        where TKey : notnull
    {
        NpgsqlDbType? keyType = PostgresVectorStoreRecordPropertyMapping.GetNpgsqlDbType(typeof(TKey)) ?? throw new ArgumentException($"Unsupported key type {typeof(TKey).Name}");

        // Generate the column names
        var columns = model.Properties
            .Where(p => includeVectors || p is not VectorStoreRecordVectorPropertyModel)
            .Select(p => p.StorageName)
            .ToList();

        var columnNames = string.Join(", ", columns.Select(c => $"\"{c}\""));
        var keyParams = string.Join(", ", keys.Select((k, i) => $"${i + 1}"));

        // Generate the SQL command
        var commandText = $"""
SELECT {columnNames}
FROM {schema}."{tableName}"
WHERE "{model.KeyProperty.StorageName}" = ANY($1);
""";

        return new PostgresSqlCommandInfo(commandText)
        {
            Parameters = [new NpgsqlParameter() { Value = keys.ToArray(), NpgsqlDbType = NpgsqlDbType.Array | keyType.Value }]
        };
    }

    /// <inheritdoc />
    internal static PostgresSqlCommandInfo BuildDeleteCommand<TKey>(string schema, string tableName, string keyColumn, TKey key)
    {
        return new PostgresSqlCommandInfo(
            commandText: $"""
DELETE FROM {schema}."{tableName}"
WHERE "{keyColumn}" = ${1};
""",
            parameters: [new NpgsqlParameter() { Value = key }]
        );
    }

    /// <inheritdoc />
    internal static PostgresSqlCommandInfo BuildDeleteBatchCommand<TKey>(string schema, string tableName, string keyColumn, List<TKey> keys)
    {
        NpgsqlDbType? keyType = PostgresVectorStoreRecordPropertyMapping.GetNpgsqlDbType(typeof(TKey)) ?? throw new ArgumentException($"Unsupported key type {typeof(TKey).Name}");

        for (int i = 0; i < keys.Count; i++)
        {
            if (keys[i] == null)
            {
                throw new ArgumentException("Keys cannot contain null values", nameof(keys));
            }
        }

        var commandText = $"""
DELETE FROM {schema}."{tableName}"
WHERE "{keyColumn}" = ANY($1);
""";

        return new PostgresSqlCommandInfo(commandText)
        {
            Parameters = [new NpgsqlParameter() { Value = keys, NpgsqlDbType = NpgsqlDbType.Array | keyType.Value }]
        };
    }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    /// <inheritdoc />
    internal static PostgresSqlCommandInfo BuildGetNearestMatchCommand<TRecord>(
        string schema, string tableName, VectorStoreRecordModel model, VectorStoreRecordVectorPropertyModel vectorProperty, Vector vectorValue,
        VectorSearchFilter? legacyFilter, Expression<Func<TRecord, bool>>? newFilter, int? skip, bool includeVectors, int limit)
    {
        var columns = string.Join(" ,", model.Properties.Select(property => $"\"{property.StorageName}\""));

        var distanceFunction = vectorProperty.DistanceFunction ?? PostgresConstants.DefaultDistanceFunction;
        var distanceOp = distanceFunction switch
        {
            DistanceFunction.CosineDistance => "<=>",
            DistanceFunction.CosineSimilarity => "<=>",
            DistanceFunction.EuclideanDistance => "<->",
            DistanceFunction.ManhattanDistance => "<+>",
            DistanceFunction.DotProductSimilarity => "<#>",
            null or "" => "<->",  // Default to Euclidean distance
            _ => throw new NotSupportedException($"Distance function {vectorProperty.DistanceFunction} is not supported.")
        };

        var vectorColumn = vectorProperty.StorageName;

        // Start where clause params at 2, vector takes param 1.
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var (where, parameters) = (oldFilter: legacyFilter, newFilter) switch
        {
            (not null, not null) => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            (not null, null) => GenerateLegacyFilterWhereClause(schema, tableName, model, legacyFilter, startParamIndex: 2),
            (null, not null) => GenerateNewFilterWhereClause(model, newFilter, startParamIndex: 2),
            _ => (Clause: string.Empty, Parameters: [])
        };
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

        var commandText = $"""
SELECT {columns}, "{vectorColumn}" {distanceOp} $1 AS "{PostgresConstants.DistanceColumnName}"
FROM {schema}."{tableName}" {where}
ORDER BY {PostgresConstants.DistanceColumnName}
LIMIT {limit}
""";

        if (skip.HasValue) { commandText += $" OFFSET {skip.Value}"; }

        // For cosine similarity, we need to take 1 - cosine distance.
        // However, we can't use an expression in the ORDER BY clause or else the index won't be used.
        // Instead we'll wrap the query in a subquery and modify the distance in the outer query.
        if (vectorProperty.DistanceFunction == DistanceFunction.CosineSimilarity)
        {
            commandText = $"""
SELECT {columns}, 1 - "{PostgresConstants.DistanceColumnName}" AS "{PostgresConstants.DistanceColumnName}"
FROM ({commandText}) AS subquery
""";
        }

        // For inner product, we need to take -1 * inner product.
        // However, we can't use an expression in the ORDER BY clause or else the index won't be used.
        // Instead we'll wrap the query in a subquery and modify the distance in the outer query.
        if (vectorProperty.DistanceFunction == DistanceFunction.DotProductSimilarity)
        {
            commandText = $"""
SELECT {columns}, -1 * "{PostgresConstants.DistanceColumnName}" AS "{PostgresConstants.DistanceColumnName}"
FROM ({commandText}) AS subquery
""";
        }

        return new PostgresSqlCommandInfo(commandText)
        {
            Parameters = [new NpgsqlParameter { Value = vectorValue }, .. parameters.Select(p => new NpgsqlParameter { Value = p })]
        };
    }

    internal static PostgresSqlCommandInfo BuildSelectWhereCommand<TRecord>(
        string schema, string tableName, VectorStoreRecordModel model,
        Expression<Func<TRecord, bool>> filter, int top, GetFilteredRecordOptions<TRecord> options)
    {
        StringBuilder query = new(200);
        query.Append("SELECT ");
        foreach (var property in model.Properties)
        {
            if (options.IncludeVectors || property is not VectorStoreRecordVectorPropertyModel)
            {
                query.AppendFormat("\"{0}\",", property.StorageName);
            }
        }
        query.Length--;  // Remove trailing comma
        query.AppendLine();
        query.AppendFormat("FROM {0}.\"{1}\"", schema, tableName).AppendLine();

        PostgresFilterTranslator translator = new(model, filter, startParamIndex: 1, query);
        translator.Translate(appendWhere: true);
        query.AppendLine();

        if (options.OrderBy.Values.Count > 0)
        {
            query.Append("ORDER BY ");

            foreach (var sortInfo in options.OrderBy.Values)
            {
                query.AppendFormat("\"{0}\" {1},",
                    model.GetDataOrKeyProperty(sortInfo.PropertySelector).StorageName,
                    sortInfo.Ascending ? "ASC" : "DESC");
            }

            query.Length--; // remove the last comma
            query.AppendLine();
        }

        query.AppendFormat("OFFSET {0}", options.Skip).AppendLine();
        query.AppendFormat("LIMIT {0}", top).AppendLine();

        return new PostgresSqlCommandInfo(query.ToString())
        {
            Parameters = translator.ParameterValues.Select(p => new NpgsqlParameter { Value = p }).ToList()
        };
    }

    internal static (string Clause, List<object> Parameters) GenerateNewFilterWhereClause(VectorStoreRecordModel model, LambdaExpression newFilter, int startParamIndex)
    {
        PostgresFilterTranslator translator = new(model, newFilter, startParamIndex);
        translator.Translate(appendWhere: true);
        return (translator.Clause.ToString(), translator.ParameterValues);
    }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    internal static (string Clause, List<object> Parameters) GenerateLegacyFilterWhereClause(string schema, string tableName, VectorStoreRecordModel model, VectorSearchFilter legacyFilter, int startParamIndex)
    {
        var whereClause = new StringBuilder("WHERE ");
        var filterClauses = new List<string>();
        var parameters = new List<object>();

        var paramIndex = startParamIndex;

        foreach (var filterClause in legacyFilter.FilterClauses)
        {
            if (filterClause is EqualToFilterClause equalTo)
            {
                var property = model.Properties.FirstOrDefault(p => p.ModelName == equalTo.FieldName);
                if (property == null) { throw new ArgumentException($"Property {equalTo.FieldName} not found in record definition."); }

                filterClauses.Add($"\"{property.StorageName}\" = ${paramIndex}");
                parameters.Add(equalTo.Value);
                paramIndex++;
            }
            else if (filterClause is AnyTagEqualToFilterClause anyTagEqualTo)
            {
                var property = model.Properties.FirstOrDefault(p => p.ModelName == anyTagEqualTo.FieldName);
                if (property == null) { throw new ArgumentException($"Property {anyTagEqualTo.FieldName} not found in record definition."); }

                if (property.Type != typeof(List<string>))
                {
                    throw new ArgumentException($"Property {anyTagEqualTo.FieldName} must be of type List<string> to use AnyTagEqualTo filter.");
                }

                filterClauses.Add($"\"{property.StorageName}\" @> ARRAY[${paramIndex}::TEXT]");
                parameters.Add(anyTagEqualTo.Value);
                paramIndex++;
            }
            else
            {
                throw new NotSupportedException($"Filter clause type {filterClause.GetType().Name} is not supported.");
            }
        }

        whereClause.Append(string.Join(" AND ", filterClauses));
        return (whereClause.ToString(), parameters);
    }
#pragma warning restore CS0618 // VectorSearchFilter is obsolete
}
