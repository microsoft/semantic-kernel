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
        createTableCommand.Append("CREATE TABLE ");
        if (ifNotExists)
        {
            createTableCommand.Append("IF NOT EXISTS ");
        }
        createTableCommand.AppendIdentifier(schema).Append('.').AppendIdentifier(tableName).AppendLine(" (");

        // Add the key column
        var keyPgTypeInfo = PostgresPropertyMapping.GetPostgresTypeName(model.KeyProperty.Type);
        createTableCommand.Append("    ").AppendIdentifier(keyName).Append(' ').Append(keyPgTypeInfo.PgType);
        if (!keyPgTypeInfo.IsNullable)
        {
            createTableCommand.Append(" NOT NULL");
        }
        createTableCommand.AppendLine(",");

        // Add the data columns
        foreach (var dataProperty in model.DataProperties)
        {
            var dataPgTypeInfo = PostgresPropertyMapping.GetPostgresTypeName(dataProperty.Type);
            createTableCommand.Append("    ").AppendIdentifier(dataProperty.StorageName).Append(' ').Append(dataPgTypeInfo.PgType);
            if (!dataPgTypeInfo.IsNullable)
            {
                createTableCommand.Append(" NOT NULL");
            }
            createTableCommand.AppendLine(",");
        }

        // Add the vector columns
        foreach (var vectorProperty in model.VectorProperties)
        {
            var vectorPgTypeInfo = PostgresPropertyMapping.GetPgVectorTypeName(vectorProperty);
            createTableCommand.Append("    ").AppendIdentifier(vectorProperty.StorageName).Append(' ').Append(vectorPgTypeInfo.PgType);
            if (!vectorPgTypeInfo.IsNullable)
            {
                createTableCommand.Append(" NOT NULL");
            }
            createTableCommand.AppendLine(",");
        }

        createTableCommand.Append("    PRIMARY KEY (").AppendIdentifier(keyName).AppendLine(")");

        createTableCommand.AppendLine(");");

        return createTableCommand.ToString();
    }

    /// <inheritdoc />
    internal static string BuildCreateIndexSql(string schema, string tableName, string columnName, string indexKind, string distanceFunction, bool isVector, bool ifNotExists)
    {
        var indexName = $"{tableName}_{columnName}_index";

        StringBuilder sql = new();
        sql.Append("CREATE INDEX ");
        if (ifNotExists)
        {
            sql.Append("IF NOT EXISTS ");
        }

        if (!isVector)
        {
            sql.AppendIdentifier(indexName).Append(" ON ").AppendIdentifier(schema).Append('.').AppendIdentifier(tableName)
                .Append(" (").AppendIdentifier(columnName).Append(')');
            return sql.ToString();
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

        sql.AppendIdentifier(indexName).Append(" ON ").AppendIdentifier(schema).Append('.').AppendIdentifier(tableName)
            .Append(" USING ").Append(indexTypeName).Append(" (").AppendIdentifier(columnName).Append(' ').Append(indexOps).Append(')');
        return sql.ToString();
    }

    /// <inheritdoc />
    internal static void BuildDropTableCommand(NpgsqlCommand command, string schema, string tableName)
    {
        StringBuilder sql = new();
        sql.Append("DROP TABLE IF EXISTS ").AppendIdentifier(schema).Append('.').AppendIdentifier(tableName);
        command.CommandText = sql.ToString();
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

        sql.Append("INSERT INTO ").AppendIdentifier(schema).Append('.').AppendIdentifier(tableName).Append(" (");

        for (var i = 0; i < model.Properties.Count; i++)
        {
            var property = model.Properties[i];

            if (i > 0)
            {
                sql.Append(", ");
            }

            sql.AppendIdentifier(property.StorageName);
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
            .Append("ON CONFLICT (").AppendIdentifier(model.KeyProperty.StorageName).Append(')');

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

            sql.Append("    ").AppendIdentifier(property.StorageName).Append(" = EXCLUDED.").AppendIdentifier(property.StorageName);
        }

        command.CommandText = sql.ToString();

        return true;
    }

    /// <inheritdoc />
    internal static void BuildGetCommand<TKey>(NpgsqlCommand command, string schema, string tableName, CollectionModel model, TKey key, bool includeVectors = false)
        where TKey : notnull
    {
        StringBuilder sql = new();
        sql.Append("SELECT ");

        for (var i = 0; i < model.Properties.Count; i++)
        {
            if (i > 0)
            {
                sql.Append(", ");
            }
            sql.AppendIdentifier(model.Properties[i].StorageName);
        }

        sql.AppendLine().Append("FROM ").AppendIdentifier(schema).Append('.').AppendIdentifier(tableName).AppendLine()
            .Append("WHERE ").AppendIdentifier(model.KeyProperty.StorageName).Append(" = $1;");

        command.CommandText = sql.ToString();
        Debug.Assert(command.Parameters.Count == 0);
        command.Parameters.Add(new() { Value = key });
    }

    /// <inheritdoc />
    internal static void BuildGetBatchCommand<TKey>(NpgsqlCommand command, string schema, string tableName, CollectionModel model, List<TKey> keys, bool includeVectors = false)
        where TKey : notnull
    {
        NpgsqlDbType? keyType = PostgresPropertyMapping.GetNpgsqlDbType(model.KeyProperty.Type) ?? throw new UnreachableException($"Unsupported key type {model.KeyProperty.Type.Name}");

        StringBuilder sql = new();
        sql.Append("SELECT ");

        var first = true;
        foreach (var property in model.Properties)
        {
            if (!includeVectors && property is VectorPropertyModel)
            {
                continue;
            }

            if (!first)
            {
                sql.Append(", ");
            }
            first = false;
            sql.AppendIdentifier(property.StorageName);
        }

        sql.AppendLine().Append("FROM ").AppendIdentifier(schema).Append('.').AppendIdentifier(tableName).AppendLine()
            .Append("WHERE ").AppendIdentifier(model.KeyProperty.StorageName).Append(" = ANY($1);");

        command.CommandText = sql.ToString();
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
        StringBuilder sql = new();
        sql.Append("DELETE FROM ").AppendIdentifier(schema).Append('.').AppendIdentifier(tableName).AppendLine()
            .Append("WHERE ").AppendIdentifier(keyColumn).Append(" = $1;");

        command.CommandText = sql.ToString();
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

        StringBuilder sql = new();
        sql.Append("DELETE FROM ").AppendIdentifier(schema).Append('.').AppendIdentifier(tableName).AppendLine()
            .Append("WHERE ").AppendIdentifier(keyColumn).Append(" = ANY($1);");

        command.CommandText = sql.ToString();
        Debug.Assert(command.Parameters.Count == 0);
        command.Parameters.Add(new() { Value = keys, NpgsqlDbType = NpgsqlDbType.Array | keyType.Value });
    }

    /// <summary>
    /// Appends a properly quoted and escaped PostgreSQL identifier to the StringBuilder.
    /// In PostgreSQL, identifiers are quoted with double quotes, and embedded double quotes are escaped by doubling them.
    /// </summary>
    internal static StringBuilder AppendIdentifier(this StringBuilder sb, string identifier)
        => sb.Append('"').Append(identifier.Replace("\"", "\"\"")).Append('"');

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    /// <inheritdoc />
    internal static void BuildGetNearestMatchCommand<TRecord>(
        NpgsqlCommand command, string schema, string tableName, CollectionModel model, VectorPropertyModel vectorProperty, object vectorValue,
        VectorSearchFilter? legacyFilter, Expression<Func<TRecord, bool>>? newFilter, int? skip, bool includeVectors, int limit)
    {
        // Build column list with proper escaping
        StringBuilder columns = new();
        for (var i = 0; i < model.Properties.Count; i++)
        {
            if (i > 0)
            {
                columns.Append(", ");
            }
            columns.AppendIdentifier(model.Properties[i].StorageName);
        }

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

        // Start where clause params at 2, vector takes param 1.
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        var (where, parameters) = (oldFilter: legacyFilter, newFilter) switch
        {
            (not null, not null) => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            (not null, null) => GenerateLegacyFilterWhereClause(model, legacyFilter, startParamIndex: 2),
            (null, not null) => GenerateNewFilterWhereClause(model, newFilter, startParamIndex: 2),
            _ => (Clause: string.Empty, Parameters: [])
        };
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

        StringBuilder sql = new();
        sql.Append("SELECT ").Append(columns).Append(", ").AppendIdentifier(vectorProperty.StorageName)
            .Append(' ').Append(distanceOp).Append(" $1 AS ").AppendIdentifier(PostgresConstants.DistanceColumnName).AppendLine()
            .Append("FROM ").AppendIdentifier(schema).Append('.').AppendIdentifier(tableName)
            .Append(' ').AppendLine(where)
            .Append("ORDER BY ").AppendLine(PostgresConstants.DistanceColumnName)
            .Append("LIMIT ").Append(limit);

        if (skip.HasValue)
        {
            sql.Append(" OFFSET ").Append(skip.Value);
        }

        var commandText = sql.ToString();

        // For cosine similarity, we need to take 1 - cosine distance.
        // However, we can't use an expression in the ORDER BY clause or else the index won't be used.
        // Instead we'll wrap the query in a subquery and modify the distance in the outer query.
        if (vectorProperty.DistanceFunction == DistanceFunction.CosineSimilarity)
        {
            StringBuilder outerSql = new();
            outerSql.Append("SELECT ").Append(columns).Append(", 1 - ").AppendIdentifier(PostgresConstants.DistanceColumnName)
                .Append(" AS ").AppendIdentifier(PostgresConstants.DistanceColumnName).AppendLine()
                .Append("FROM (").Append(commandText).Append(") AS subquery");
            commandText = outerSql.ToString();
        }

        // For inner product, we need to take -1 * inner product.
        // However, we can't use an expression in the ORDER BY clause or else the index won't be used.
        // Instead we'll wrap the query in a subquery and modify the distance in the outer query.
        if (vectorProperty.DistanceFunction == DistanceFunction.DotProductSimilarity)
        {
            StringBuilder outerSql = new();
            outerSql.Append("SELECT ").Append(columns).Append(", -1 * ").AppendIdentifier(PostgresConstants.DistanceColumnName)
                .Append(" AS ").AppendIdentifier(PostgresConstants.DistanceColumnName).AppendLine()
                .Append("FROM (").Append(commandText).Append(") AS subquery");
            commandText = outerSql.ToString();
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
        var first = true;
        foreach (var property in model.Properties)
        {
            if (options.IncludeVectors || property is not VectorPropertyModel)
            {
                if (!first)
                {
                    query.Append(',');
                }
                first = false;
                query.AppendIdentifier(property.StorageName);
            }
        }
        query.AppendLine();
        query.Append("FROM ").AppendIdentifier(schema).Append('.').AppendIdentifier(tableName).AppendLine();

        PostgresFilterTranslator translator = new(model, filter, startParamIndex: 1, query);
        translator.Translate(appendWhere: true);
        query.AppendLine();

        var orderBy = options.OrderBy?.Invoke(new()).Values;
        if (orderBy is { Count: > 0 })
        {
            query.Append("ORDER BY ");

            var firstOrderBy = true;
            foreach (var sortInfo in orderBy)
            {
                if (!firstOrderBy)
                {
                    query.Append(',');
                }
                firstOrderBy = false;
                query.AppendIdentifier(model.GetDataOrKeyProperty(sortInfo.PropertySelector).StorageName)
                    .Append(sortInfo.Ascending ? " ASC" : " DESC");
            }

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
    internal static (string Clause, List<object> Parameters) GenerateLegacyFilterWhereClause(CollectionModel model, VectorSearchFilter legacyFilter, int startParamIndex)
    {
        StringBuilder whereClause = new("WHERE ");
        var parameters = new List<object>();

        var paramIndex = startParamIndex;
        var first = true;

        foreach (var filterClause in legacyFilter.FilterClauses)
        {
            if (!first)
            {
                whereClause.Append(" AND ");
            }
            first = false;

            if (filterClause is EqualToFilterClause equalTo)
            {
                var property = model.Properties.FirstOrDefault(p => p.ModelName == equalTo.FieldName);
                if (property == null) { throw new ArgumentException($"Property {equalTo.FieldName} not found in record definition."); }

                whereClause.AppendIdentifier(property.StorageName).Append(" = $").Append(paramIndex);
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

                whereClause.AppendIdentifier(property.StorageName).Append(" @> ARRAY[$").Append(paramIndex).Append("::TEXT]");
                parameters.Add(anyTagEqualTo.Value);
                paramIndex++;
            }
            else
            {
                throw new NotSupportedException($"Filter clause type {filterClause.GetType().Name} is not supported.");
            }
        }

        return (whereClause.ToString(), parameters);
    }
#pragma warning restore CS0618 // VectorSearchFilter is obsolete
}
