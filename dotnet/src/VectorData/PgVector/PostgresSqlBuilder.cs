// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Text;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Npgsql;
using NpgsqlTypes;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// Provides methods to build SQL commands for managing vector store collections in PostgreSQL.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "We need to build the full table name using schema and collection, it does not support parameterized passing.")]
internal static class PostgresSqlBuilder
{
    internal static void BuildDoesTableExistCommand(NpgsqlCommand command, string schema, string tableName)
    {
        command.CommandText = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = $1
    AND table_type = 'BASE TABLE'
    AND table_name = $2
""";

        Debug.Assert(command.Parameters.Count == 0);
        command.Parameters.Add(new() { Value = schema });
        command.Parameters.Add(new() { Value = tableName });
    }

    internal static void BuildGetTablesCommand(NpgsqlCommand command, string schema)
    {
        command.CommandText = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = $1 AND table_type = 'BASE TABLE'
""";
        Debug.Assert(command.Parameters.Count == 0);
        command.Parameters.Add(new() { Value = schema });
    }

    internal static string BuildCreateTableSql(string schema, string tableName, CollectionModel model, bool ifNotExists = true)
    {
        if (string.IsNullOrWhiteSpace(tableName))
        {
            throw new ArgumentException("Table name cannot be null or whitespace", nameof(tableName));
        }

        var keyName = model.KeyProperty.StorageName;

        StringBuilder createTableCommand = new();
        createTableCommand.AppendLine($"CREATE TABLE {(ifNotExists ? "IF NOT EXISTS " : "")}{schema}.\"{tableName}\" (");

        // Add the key column
        var keyPgTypeInfo = PostgresPropertyMapping.GetPostgresTypeName(model.KeyProperty.Type);
        createTableCommand.AppendLine($"    \"{keyName}\" {keyPgTypeInfo.PgType}{(keyPgTypeInfo.IsNullable ? "" : " NOT NULL")},");

        // Add the data columns
        foreach (var dataProperty in model.DataProperties)
        {
            string columnName = dataProperty.StorageName;
            var dataPgTypeInfo = PostgresPropertyMapping.GetPostgresTypeName(dataProperty.Type);
            createTableCommand.AppendLine($"    \"{columnName}\" {dataPgTypeInfo.PgType}{(dataPgTypeInfo.IsNullable ? "" : " NOT NULL")},");
        }

        // Add the vector columns
        foreach (var vectorProperty in model.VectorProperties)
        {
            string columnName = vectorProperty.StorageName;
            var vectorPgTypeInfo = PostgresPropertyMapping.GetPgVectorTypeName(vectorProperty);
            createTableCommand.AppendLine($"    \"{columnName}\" {vectorPgTypeInfo.PgType}{(vectorPgTypeInfo.IsNullable ? "" : " NOT NULL")},");
        }

        createTableCommand.AppendLine($"    PRIMARY KEY (\"{keyName}\")");

        createTableCommand.AppendLine(");");

        return createTableCommand.ToString();
    }

    /// <inheritdoc />
    internal static string BuildCreateIndexSql(string schema, string tableName, string columnName, string indexKind, string distanceFunction, bool isVector, bool ifNotExists)
    {
        var indexName = $"{tableName}_{columnName}_index";

        if (!isVector)
        {
            return $@"CREATE INDEX {(ifNotExists ? "IF NOT EXISTS " : "")}""{indexName}"" ON {schema}.""{tableName}"" (""{columnName}"")";
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
            DistanceFunction.HammingDistance => "bit_hamming_ops",

            _ => throw new NotSupportedException($"Distance function {distanceFunction} is not supported.")
        };

        return $@"CREATE INDEX {(ifNotExists ? "IF NOT EXISTS " : "")} ""{indexName}"" ON {schema}.""{tableName}"" USING {indexTypeName} (""{columnName}"" {indexOps})";
    }

    /// <inheritdoc />
    internal static void BuildDropTableCommand(NpgsqlCommand command, string schema, string tableName)
    {
        command.CommandText = $@"DROP TABLE IF EXISTS {schema}.""{tableName}""";
    }

    /// <inheritdoc />
    internal static bool BuildUpsertCommand(
        NpgsqlCommand command,
        string schema,
        string tableName,
        CollectionModel model,
        IEnumerable<object> records,
        Dictionary<VectorPropertyModel, IReadOnlyList<Embedding>>? generatedEmbeddings)
    {
        StringBuilder sql = new();

        sql
            .Append("INSERT INTO ")
            .Append(schema)
            .Append(".\"")
            .Append(tableName)
            .Append("\" (");

        for (var i = 0; i < model.Properties.Count; i++)
        {
            var property = model.Properties[i];

            if (i > 0)
            {
                sql.Append(", ");
            }

            sql.Append('"').Append(property.StorageName).Append('"');
        }

        sql
            .AppendLine(")")
            .Append("VALUES ");

        var recordIndex = 0;
        var parameterIndex = 1;

        foreach (var record in records)
        {
            if (recordIndex > 0)
            {
                sql.Append(", ");
            }

            sql.Append('(');

            for (var i = 0; i < model.Properties.Count; i++)
            {
                var property = model.Properties[i];

                if (i > 0)
                {
                    sql.Append(", ");
                }

                var value = property.GetValueAsObject(record);

                if (property is VectorPropertyModel vectorProperty)
                {
                    if (generatedEmbeddings?[vectorProperty] is IReadOnlyList<Embedding> ge)
                    {
                        value = ge[recordIndex];
                    }

                    value = PostgresPropertyMapping.MapVectorForStorageModel(value);
                }

                command.Parameters.Add(new() { Value = value ?? DBNull.Value });
                sql.Append('$').Append(parameterIndex++);
            }

            sql.Append(')');

            recordIndex++;
        }

        // No records to insert, return false to indicate no command was built.
        if (recordIndex == 0)
        {
            return false;
        }

        sql
            .AppendLine()
            .Append("ON CONFLICT (\"")
            .Append(model.KeyProperty.StorageName)
            .Append("\")");

        sql
            .AppendLine()
            .AppendLine("DO UPDATE SET ");

        var propertyIndex = 0;
        foreach (var property in model.Properties)
        {
            if (property is KeyPropertyModel)
            {
                continue;
            }

            if (propertyIndex++ > 0)
            {
                sql.AppendLine(", ");
            }

            sql
                .Append("    \"")
                .Append(property.StorageName)
                .Append("\" = EXCLUDED.\"")
                .Append(property.StorageName)
                .Append('"');
        }

        command.CommandText = sql.ToString();

        return true;
    }

    /// <inheritdoc />
    internal static void BuildGetCommand<TKey>(NpgsqlCommand command, string schema, string tableName, CollectionModel model, TKey key, bool includeVectors = false)
        where TKey : notnull
    {
        List<string> queryColumns = new();

        foreach (var property in model.Properties)
        {
            queryColumns.Add($"\"{property.StorageName}\"");
        }

        var queryColumnList = string.Join(", ", queryColumns);

        command.CommandText = $"""
SELECT {queryColumnList}
FROM {schema}."{tableName}"
WHERE "{model.KeyProperty.StorageName}" = ${1};
""";
        Debug.Assert(command.Parameters.Count == 0);
        command.Parameters.Add(new() { Value = key });
    }

    /// <inheritdoc />
    internal static void BuildGetBatchCommand<TKey>(NpgsqlCommand command, string schema, string tableName, CollectionModel model, List<TKey> keys, bool includeVectors = false)
        where TKey : notnull
    {
        NpgsqlDbType? keyType = PostgresPropertyMapping.GetNpgsqlDbType(model.KeyProperty.Type) ?? throw new UnreachableException($"Unsupported key type {typeof(TKey).Name}");

        // Generate the column names
        var columns = model.Properties
            .Where(p => includeVectors || p is not VectorPropertyModel)
            .Select(p => p.StorageName)
            .ToList();

        var columnNames = string.Join(", ", columns.Select(c => $"\"{c}\""));
        var keyParams = string.Join(", ", keys.Select((k, i) => $"${i + 1}"));

        command.CommandText = $"""
SELECT {columnNames}
FROM {schema}."{tableName}"
WHERE "{model.KeyProperty.StorageName}" = ANY($1);
""";

        Debug.Assert(command.Parameters.Count == 0);
        command.Parameters.Add(new()
        {
            Value = keys.ToArray(),
            NpgsqlDbType = NpgsqlDbType.Array | keyType.Value
        });
    }

    /// <inheritdoc />
    internal static void BuildDeleteCommand<TKey>(NpgsqlCommand command, string schema, string tableName, string keyColumn, TKey key)
    {
        command.CommandText = $"""
DELETE FROM {schema}."{tableName}"
WHERE "{keyColumn}" = ${1};
""";
        Debug.Assert(command.Parameters.Count == 0);
        command.Parameters.Add(new() { Value = key });
    }

    /// <inheritdoc />
    internal static void BuildDeleteBatchCommand<TKey>(NpgsqlCommand command, string schema, string tableName, string keyColumn, List<TKey> keys)
    {
        NpgsqlDbType? keyType = PostgresPropertyMapping.GetNpgsqlDbType(typeof(TKey)) ?? throw new ArgumentException($"Unsupported key type {typeof(TKey).Name}");

        for (int i = 0; i < keys.Count; i++)
        {
            if (keys[i] == null)
            {
                throw new ArgumentException("Keys cannot contain null values", nameof(keys));
            }
        }

        command.CommandText = $"""
DELETE FROM {schema}."{tableName}"
WHERE "{keyColumn}" = ANY($1);
""";

        Debug.Assert(command.Parameters.Count == 0);
        command.Parameters.Add(new() { Value = keys, NpgsqlDbType = NpgsqlDbType.Array | keyType.Value });
    }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    /// <inheritdoc />
    internal static void BuildGetNearestMatchCommand<TRecord>(
        NpgsqlCommand command, string schema, string tableName, CollectionModel model, VectorPropertyModel vectorProperty, object vectorValue,
        VectorSearchFilter? legacyFilter, Expression<Func<TRecord, bool>>? newFilter, int? skip, bool includeVectors, int limit)
    {
        var columns = string.Join(" ,", model.Properties.Select(property => $"\"{property.StorageName}\""));

        var distanceFunction = vectorProperty.DistanceFunction ?? PostgresConstants.DefaultDistanceFunction;
        var distanceOp = distanceFunction switch
        {
            DistanceFunction.EuclideanDistance or null => "<->",
            DistanceFunction.CosineDistance or DistanceFunction.CosineSimilarity => "<=>",
            DistanceFunction.ManhattanDistance => "<+>",
            DistanceFunction.DotProductSimilarity => "<#>",
            DistanceFunction.HammingDistance => "<~>",

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

        command.CommandText = commandText;

        Debug.Assert(command.Parameters.Count == 0);
        command.Parameters.Add(new NpgsqlParameter { Value = vectorValue });

        foreach (var parameter in parameters)
        {
            command.Parameters.Add(new NpgsqlParameter { Value = parameter });
        }
    }

    internal static void BuildSelectWhereCommand<TRecord>(
        NpgsqlCommand command, string schema, string tableName, CollectionModel model,
        Expression<Func<TRecord, bool>> filter, int top, FilteredRecordRetrievalOptions<TRecord> options)
    {
        StringBuilder query = new(200);
        query.Append("SELECT ");
        foreach (var property in model.Properties)
        {
            if (options.IncludeVectors || property is not VectorPropertyModel)
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

        var orderBy = options.OrderBy?.Invoke(new()).Values;
        if (orderBy is { Count: > 0 })
        {
            query.Append("ORDER BY ");

            foreach (var sortInfo in orderBy)
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

        command.CommandText = query.ToString();

        Debug.Assert(command.Parameters.Count == 0);
        foreach (var parameter in translator.ParameterValues)
        {
            command.Parameters.Add(new NpgsqlParameter { Value = parameter });
        }
    }

    internal static (string Clause, List<object> Parameters) GenerateNewFilterWhereClause(CollectionModel model, LambdaExpression newFilter, int startParamIndex)
    {
        PostgresFilterTranslator translator = new(model, newFilter, startParamIndex);
        translator.Translate(appendWhere: true);
        return (translator.Clause.ToString(), translator.ParameterValues);
    }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    internal static (string Clause, List<object> Parameters) GenerateLegacyFilterWhereClause(string schema, string tableName, CollectionModel model, VectorSearchFilter legacyFilter, int startParamIndex)
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
