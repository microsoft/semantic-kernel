// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.VectorData;
using Npgsql;
using NpgsqlTypes;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Provides methods to build SQL commands for managing vector store collections in PostgreSQL.
/// </summary>
internal class PostgresVectorStoreCollectionSqlBuilder : IPostgresVectorStoreCollectionSqlBuilder
{
    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildDoesTableExistCommand(string schema, string tableName)
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
    public PostgresSqlCommandInfo BuildGetTablesCommand(string schema)
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
    public PostgresSqlCommandInfo BuildCreateTableCommand(string schema, string tableName, IReadOnlyList<VectorStoreRecordProperty> properties, bool ifNotExists = true)
    {
        if (string.IsNullOrWhiteSpace(tableName))
        {
            throw new ArgumentException("Table name cannot be null or whitespace", nameof(tableName));
        }

        VectorStoreRecordKeyProperty? keyProperty = default;
        List<VectorStoreRecordDataProperty> dataProperties = new();
        List<VectorStoreRecordVectorProperty> vectorProperties = new();

        foreach (var property in properties)
        {
            if (property is VectorStoreRecordKeyProperty keyProp)
            {
                if (keyProperty != null)
                {
                    // Should be impossible, as property reader should have already validated that
                    // multiple key properties are not allowed.
                    throw new ArgumentException("Record definition cannot have more than one key property.");
                }
                keyProperty = keyProp;
            }
            else if (property is VectorStoreRecordDataProperty dataProp)
            {
                dataProperties.Add(dataProp);
            }
            else if (property is VectorStoreRecordVectorProperty vectorProp)
            {
                vectorProperties.Add(vectorProp);
            }
            else
            {
                throw new NotSupportedException($"Property type {property.GetType().Name} is not supported by this store.");
            }
        }

        if (keyProperty == null)
        {
            throw new ArgumentException("Record definition must have a key property.");
        }

        var keyName = keyProperty.StoragePropertyName ?? keyProperty.DataModelPropertyName;

        StringBuilder createTableCommand = new();
        createTableCommand.AppendLine($"CREATE TABLE {(ifNotExists ? "IF NOT EXISTS " : "")}{schema}.\"{tableName}\" (");

        // Add the key column
        var keyPgTypeInfo = PostgresVectorStoreRecordPropertyMapping.GetPostgresTypeName(keyProperty.PropertyType);
        createTableCommand.AppendLine($"    \"{keyName}\" {keyPgTypeInfo.PgType} {(keyPgTypeInfo.IsNullable ? "" : "NOT NULL")},");

        // Add the data columns
        foreach (var dataProperty in dataProperties)
        {
            string columnName = dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName;
            var dataPgTypeInfo = PostgresVectorStoreRecordPropertyMapping.GetPostgresTypeName(dataProperty.PropertyType);
            createTableCommand.AppendLine($"    \"{columnName}\" {dataPgTypeInfo.PgType} {(dataPgTypeInfo.IsNullable ? "" : "NOT NULL")},");
        }

        // Add the vector columns
        foreach (var vectorProperty in vectorProperties)
        {
            string columnName = vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName;
            var vectorPgTypeInfo = PostgresVectorStoreRecordPropertyMapping.GetPgVectorTypeName(vectorProperty);
            createTableCommand.AppendLine($"    \"{columnName}\" {vectorPgTypeInfo.PgType} {(vectorPgTypeInfo.IsNullable ? "" : "NOT NULL")},");
        }

        createTableCommand.AppendLine($"    PRIMARY KEY (\"{keyName}\")");

        createTableCommand.AppendLine(");");

        return new PostgresSqlCommandInfo(commandText: createTableCommand.ToString());
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildCreateVectorIndexCommand(string schema, string tableName, string vectorColumnName, string indexKind, string distanceFunction, bool ifNotExists)
    {
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

        var indexName = $"{tableName}_{vectorColumnName}_index";

        return new PostgresSqlCommandInfo(
            commandText: $@"
                CREATE INDEX {(ifNotExists ? "IF NOT EXISTS " : "")} ""{indexName}"" ON {schema}.""{tableName}"" USING {indexTypeName} (""{vectorColumnName}"" {indexOps});"
        );
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildDropTableCommand(string schema, string tableName)
    {
        return new PostgresSqlCommandInfo(
            commandText: $@"DROP TABLE IF EXISTS {schema}.""{tableName}"""
        );
    }

    /// <inheritdoc/>
    public PostgresSqlCommandInfo BuildUpsertCommand(string schema, string tableName, string keyColumn, Dictionary<string, object?> row)
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
    public PostgresSqlCommandInfo BuildUpsertBatchCommand(string schema, string tableName, string keyColumn, List<Dictionary<string, object?>> rows)
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
    public PostgresSqlCommandInfo BuildGetCommand<TKey>(string schema, string tableName, IReadOnlyList<VectorStoreRecordProperty> properties, TKey key, bool includeVectors = false)
        where TKey : notnull
    {
        List<string> queryColumns = new();
        string? keyColumn = null;

        foreach (var property in properties)
        {
            if (property is VectorStoreRecordKeyProperty keyProperty)
            {
                if (keyColumn != null)
                {
                    throw new ArgumentException("Record definition cannot have more than one key property.");
                }
                keyColumn = keyProperty.StoragePropertyName ?? keyProperty.DataModelPropertyName;
                queryColumns.Add($"\"{keyColumn}\"");
            }
            else if (property is VectorStoreRecordDataProperty dataProperty)
            {
                string columnName = dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName;
                queryColumns.Add($"\"{columnName}\"");
            }
            else if (property is VectorStoreRecordVectorProperty vectorProperty && includeVectors)
            {
                string columnName = vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName;
                queryColumns.Add($"\"{columnName}\"");
            }
        }

        Verify.NotNull(keyColumn, "Record definition must have a key property.");

        var queryColumnList = string.Join(", ", queryColumns);

        return new PostgresSqlCommandInfo(
            commandText: $"""
SELECT {queryColumnList}
FROM {schema}."{tableName}"
WHERE "{keyColumn}" = ${1};
""",
            parameters: [new NpgsqlParameter() { Value = key }]
        );
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildGetBatchCommand<TKey>(string schema, string tableName, IReadOnlyList<VectorStoreRecordProperty> properties, List<TKey> keys, bool includeVectors = false)
        where TKey : notnull
    {
        NpgsqlDbType? keyType = PostgresVectorStoreRecordPropertyMapping.GetNpgsqlDbType(typeof(TKey)) ?? throw new ArgumentException($"Unsupported key type {typeof(TKey).Name}");

        var keyProperty = properties.OfType<VectorStoreRecordKeyProperty>().FirstOrDefault() ?? throw new ArgumentException("Properties must contain a key property", nameof(properties));
        var keyColumn = keyProperty.StoragePropertyName ?? keyProperty.DataModelPropertyName;

        // Generate the column names
        var columns = properties
            .Where(p => includeVectors || p is not VectorStoreRecordVectorProperty)
            .Select(p => p.StoragePropertyName ?? p.DataModelPropertyName)
            .ToList();

        var columnNames = string.Join(", ", columns.Select(c => $"\"{c}\""));
        var keyParams = string.Join(", ", keys.Select((k, i) => $"${i + 1}"));

        // Generate the SQL command
        var commandText = $"""
SELECT {columnNames}
FROM {schema}."{tableName}"
WHERE "{keyColumn}" = ANY($1);
""";

        return new PostgresSqlCommandInfo(commandText)
        {
            Parameters = [new NpgsqlParameter() { Value = keys.ToArray(), NpgsqlDbType = NpgsqlDbType.Array | keyType.Value }]
        };
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildDeleteCommand<TKey>(string schema, string tableName, string keyColumn, TKey key)
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
    public PostgresSqlCommandInfo BuildDeleteBatchCommand<TKey>(string schema, string tableName, string keyColumn, List<TKey> keys)
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
    public PostgresSqlCommandInfo BuildGetNearestMatchCommand<TRecord>(
        string schema, string tableName, VectorStoreRecordPropertyReader propertyReader, VectorStoreRecordVectorProperty vectorProperty, Vector vectorValue,
        VectorSearchFilter? legacyFilter, Expression<Func<TRecord, bool>>? newFilter, int? skip, bool includeVectors, int limit)
    {
        var columns = string.Join(" ,",
            propertyReader.RecordDefinition.Properties
                .Select(property => property.StoragePropertyName ?? property.DataModelPropertyName)
                .Select(column => $"\"{column}\"")
        );

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

        var vectorColumn = vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName;

        // Start where clause params at 2, vector takes param 1.
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var (where, parameters) = (oldFilter: legacyFilter, newFilter) switch
        {
            (not null, not null) => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            (not null, null) => GenerateLegacyFilterWhereClause(schema, tableName, propertyReader.RecordDefinition.Properties, legacyFilter, startParamIndex: 2),
            (null, not null) => GenerateNewFilterWhereClause(propertyReader, newFilter),
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

    internal static (string Clause, List<object> Parameters) GenerateNewFilterWhereClause(VectorStoreRecordPropertyReader propertyReader, LambdaExpression newFilter)
    {
        PostgresFilterTranslator translator = new(propertyReader.StoragePropertyNamesMap, newFilter, startParamIndex: 2);
        translator.Translate(appendWhere: true);
        return (translator.Clause.ToString(), translator.ParameterValues);
    }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    internal static (string Clause, List<object> Parameters) GenerateLegacyFilterWhereClause(string schema, string tableName, IReadOnlyList<VectorStoreRecordProperty> properties, VectorSearchFilter legacyFilter, int startParamIndex)
    {
        var whereClause = new StringBuilder("WHERE ");
        var filterClauses = new List<string>();
        var parameters = new List<object>();

        var paramIndex = startParamIndex;

        foreach (var filterClause in legacyFilter.FilterClauses)
        {
            if (filterClause is EqualToFilterClause equalTo)
            {
                var property = properties.FirstOrDefault(p => p.DataModelPropertyName == equalTo.FieldName);
                if (property == null) { throw new ArgumentException($"Property {equalTo.FieldName} not found in record definition."); }

                var columnName = property.StoragePropertyName ?? property.DataModelPropertyName;
                filterClauses.Add($"\"{columnName}\" = ${paramIndex}");
                parameters.Add(equalTo.Value);
                paramIndex++;
            }
            else if (filterClause is AnyTagEqualToFilterClause anyTagEqualTo)
            {
                var property = properties.FirstOrDefault(p => p.DataModelPropertyName == anyTagEqualTo.FieldName);
                if (property == null) { throw new ArgumentException($"Property {anyTagEqualTo.FieldName} not found in record definition."); }

                if (property.PropertyType != typeof(List<string>))
                {
                    throw new ArgumentException($"Property {anyTagEqualTo.FieldName} must be of type List<string> to use AnyTagEqualTo filter.");
                }

                var columnName = property.StoragePropertyName ?? property.DataModelPropertyName;
                filterClauses.Add($"\"{columnName}\" @> ARRAY[${paramIndex}::TEXT]");
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
