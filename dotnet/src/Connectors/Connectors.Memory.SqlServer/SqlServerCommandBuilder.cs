// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

#pragma warning disable CA2100 // Review SQL queries for security vulnerabilities

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal static class SqlServerCommandBuilder
{
    internal static SqlCommand CreateTable(
        SqlConnection connection,
        string? schema,
        string tableName,
        bool ifNotExists,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordDataProperty> dataProperties,
        IReadOnlyList<VectorStoreRecordVectorProperty> vectorProperties)
    {
        StringBuilder sb = new(200);
        if (ifNotExists)
        {
            sb.Append("IF OBJECT_ID(N'");
            sb.AppendTableName(schema, tableName);
            sb.AppendLine("', N'U') IS NULL");
        }
        sb.AppendLine("BEGIN");
        sb.Append("CREATE TABLE ");
        sb.AppendTableName(schema, tableName);
        sb.AppendLine(" (");
        string keyColumnName = GetColumnName(keyProperty);
        var keyMapping = Map(keyProperty.PropertyType);
        sb.AppendFormat("[{0}] {1} NOT NULL,", keyColumnName, keyMapping.sqlName);
        sb.AppendLine();
        for (int i = 0; i < dataProperties.Count; i++)
        {
            sb.AppendFormat("[{0}] {1},", GetColumnName(dataProperties[i]), Map(dataProperties[i].PropertyType).sqlName);
            sb.AppendLine();
        }
        for (int i = 0; i < vectorProperties.Count; i++)
        {
            sb.AppendFormat("[{0}] VECTOR({1}),", GetColumnName(vectorProperties[i]), vectorProperties[i].Dimensions);
            sb.AppendLine();
        }
        sb.AppendFormat("PRIMARY KEY ([{0}])", keyColumnName);
        sb.AppendLine();
        sb.AppendLine(");"); // end the table definition

        foreach (var vectorProperty in vectorProperties)
        {
            switch (vectorProperty.IndexKind)
            {
                case null:
                case "":
                case IndexKind.Flat:
                    break;
                default:
                    throw new NotSupportedException($"Index kind {vectorProperty.IndexKind} is not supported.");
            }
        }
        sb.Append("END;");

        return connection.CreateCommand(sb);
    }

    internal static SqlCommand DropTableIfExists(SqlConnection connection, string? schema, string tableName)
    {
        StringBuilder sb = new(50);
        sb.Append("DROP TABLE IF EXISTS ");
        sb.AppendTableName(schema, tableName);

        return connection.CreateCommand(sb);
    }

    internal static SqlCommand SelectTableName(SqlConnection connection, string? schema, string tableName)
    {
        SqlCommand command = connection.CreateCommand();
        command.CommandText = """
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                    AND (@schema is NULL or TABLE_SCHEMA = @schema)
                    AND TABLE_NAME = @tableName
                """;
        command.Parameters.AddWithValue("@schema", string.IsNullOrEmpty(schema) ? DBNull.Value : schema);
        command.Parameters.AddWithValue("@tableName", tableName); // the name is not escaped by us, just provided as parameter
        return command;
    }

    internal static SqlCommand SelectTableNames(SqlConnection connection, string? schema)
    {
        SqlCommand command = connection.CreateCommand();
        command.CommandText = """
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                    AND (@schema is NULL or TABLE_SCHEMA = @schema)
                """;
        command.Parameters.AddWithValue("@schema", string.IsNullOrEmpty(schema) ? DBNull.Value : schema);
        return command;
    }

    internal static SqlCommand MergeIntoSingle(
        SqlConnection connection,
        string? schema,
        string tableName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordProperty> properties,
        IDictionary<string, object?> record)
    {
        SqlCommand command = connection.CreateCommand();
        StringBuilder sb = new(200);
        sb.Append("MERGE INTO ");
        sb.AppendTableName(schema, tableName);
        sb.AppendLine(" AS t");
        sb.Append("USING (VALUES (");
        int paramIndex = 0;
        foreach (VectorStoreRecordProperty property in properties)
        {
            sb.AppendParameterName(property, ref paramIndex, out string paramName).Append(',');
            command.AddParameter(property, paramName, record[GetColumnName(property)]);
        }
        sb[sb.Length - 1] = ')'; // replace the last comma with a closing parenthesis
        sb.Append(") AS s (");
        sb.AppendColumnNames(properties);
        sb.AppendLine(")");
        sb.AppendFormat("ON (t.[{0}] = s.[{0}])", GetColumnName(keyProperty)).AppendLine();
        sb.AppendLine("WHEN MATCHED THEN");
        sb.Append("UPDATE SET ");
        foreach (VectorStoreRecordProperty property in properties)
        {
            if (property != keyProperty) // don't update the key
            {
                sb.AppendFormat("t.[{0}] = s.[{0}],", GetColumnName(property));
            }
        }
        --sb.Length; // remove the last comma
        sb.AppendLine();

        sb.Append("WHEN NOT MATCHED THEN");
        sb.AppendLine();
        sb.Append("INSERT (");
        sb.AppendColumnNames(properties);
        sb.AppendLine(")");
        sb.Append("VALUES (");
        sb.AppendColumnNames(properties, prefix: "s.");
        sb.AppendLine(")");
        sb.AppendFormat("OUTPUT inserted.[{0}];", GetColumnName(keyProperty));

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand? MergeIntoMany(
        SqlConnection connection,
        string? schema,
        string tableName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordProperty> properties,
        IEnumerable<IDictionary<string, object?>> records)
    {
        SqlCommand command = connection.CreateCommand();

        StringBuilder sb = new(200);
        // The DECLARE statement creates a table variable to store the keys of the inserted rows.
        sb.AppendFormat("DECLARE @InsertedKeys TABLE (KeyColumn {0});", Map(keyProperty.PropertyType).sqlName);
        sb.AppendLine();
        // The MERGE statement performs the upsert operation and outputs the keys of the inserted rows into the table variable.
        sb.Append("MERGE INTO ");
        sb.AppendTableName(schema, tableName);
        sb.AppendLine(" AS t"); // t stands for target
        sb.AppendLine("USING (VALUES");
        int rowIndex = 0, paramIndex = 0;
        foreach (var record in records)
        {
            sb.Append('(');
            foreach (VectorStoreRecordProperty property in properties)
            {
                sb.AppendParameterName(property, ref paramIndex, out string paramName).Append(',');
                command.AddParameter(property, paramName, record[GetColumnName(property)]);
            }
            sb[sb.Length - 1] = ')'; // replace the last comma with a closing parenthesis
            sb.AppendLine(",");
            rowIndex++;
        }

        if (rowIndex == 0)
        {
            return null; // there is nothing to do!
        }

        sb.Length -= (1 + Environment.NewLine.Length); // remove the last comma and newline

        sb.Append(") AS s ("); // s stands for source
        sb.AppendColumnNames(properties);
        sb.AppendLine(")");
        sb.AppendFormat("ON (t.[{0}] = s.[{0}])", GetColumnName(keyProperty)).AppendLine();
        sb.AppendLine("WHEN MATCHED THEN");
        sb.Append("UPDATE SET ");
        foreach (VectorStoreRecordProperty property in properties)
        {
            if (property != keyProperty) // don't update the key
            {
                sb.AppendFormat("t.[{0}] = s.[{0}],", GetColumnName(property));
            }
        }
        --sb.Length; // remove the last comma
        sb.AppendLine();
        sb.Append("WHEN NOT MATCHED THEN");
        sb.AppendLine();
        sb.Append("INSERT (");
        sb.AppendColumnNames(properties);
        sb.AppendLine(")");
        sb.Append("VALUES (");
        sb.AppendColumnNames(properties, prefix: "s.");
        sb.AppendLine(")");
        sb.AppendFormat("OUTPUT inserted.[{0}] INTO @InsertedKeys (KeyColumn);", GetColumnName(keyProperty));
        sb.AppendLine();

        // The SELECT statement returns the keys of the inserted rows.
        sb.Append("SELECT KeyColumn FROM @InsertedKeys;");

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand DeleteSingle(
        SqlConnection connection, string? schema, string tableName,
        VectorStoreRecordKeyProperty keyProperty, object key)
    {
        SqlCommand command = connection.CreateCommand();

        int paramIndex = 0;
        StringBuilder sb = new(100);
        sb.Append("DELETE FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendFormat(" WHERE [{0}] = ", GetColumnName(keyProperty));
        sb.AppendParameterName(keyProperty, ref paramIndex, out string keyParamName);
        command.AddParameter(keyProperty, keyParamName, key);

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand? DeleteMany<TKey>(
        SqlConnection connection, string? schema, string tableName,
        VectorStoreRecordKeyProperty keyProperty, IEnumerable<TKey> keys)
    {
        SqlCommand command = connection.CreateCommand();

        StringBuilder sb = new(100);
        sb.Append("DELETE FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendFormat(" WHERE [{0}] IN (", GetColumnName(keyProperty));
        sb.AppendKeyParameterList(keys, command, keyProperty, out bool emptyKeys);
        sb.Append(')'); // close the IN clause

        if (emptyKeys)
        {
            return null; // there is nothing to do!
        }

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand SelectSingle(
        SqlConnection sqlConnection, string? schema, string collectionName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordProperty> properties,
        object key,
        bool includeVectors)
    {
        SqlCommand command = sqlConnection.CreateCommand();

        int paramIndex = 0;
        StringBuilder sb = new(200);
        sb.AppendFormat("SELECT ");
        sb.AppendColumnNames(properties, includeVectors: includeVectors);
        sb.AppendLine();
        sb.Append("FROM ");
        sb.AppendTableName(schema, collectionName);
        sb.AppendLine();
        sb.AppendFormat("WHERE [{0}] = ", GetColumnName(keyProperty));
        sb.AppendParameterName(keyProperty, ref paramIndex, out string keyParamName);
        command.AddParameter(keyProperty, keyParamName, key);

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand? SelectMany<TKey>(
        SqlConnection connection, string? schema, string tableName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordProperty> properties,
        IEnumerable<TKey> keys,
        bool includeVectors)
    {
        SqlCommand command = connection.CreateCommand();

        StringBuilder sb = new(200);
        sb.AppendFormat("SELECT ");
        sb.AppendColumnNames(properties, includeVectors: includeVectors);
        sb.AppendLine();
        sb.Append("FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendLine();
        sb.AppendFormat("WHERE [{0}] IN (", GetColumnName(keyProperty));
        sb.AppendKeyParameterList(keys, command, keyProperty, out bool emptyKeys);
        sb.Append(')'); // close the IN clause

        if (emptyKeys)
        {
            return null; // there is nothing to do!
        }

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand SelectVector<TRecord>(
        SqlConnection connection, string? schema, string tableName,
        VectorStoreRecordVectorProperty vectorProperty,
        IReadOnlyList<VectorStoreRecordProperty> properties,
        IReadOnlyDictionary<string, string> storagePropertyNamesMap,
        VectorSearchOptions<TRecord> options,
        ReadOnlyMemory<float> vector)
    {
        string distanceFunction = vectorProperty.DistanceFunction ?? DistanceFunction.CosineDistance;
        (string distanceMetric, string sorting) = MapDistanceFunction(distanceFunction);

        SqlCommand command = connection.CreateCommand();
        command.Parameters.AddWithValue("@vector", JsonSerializer.Serialize(vector));

        StringBuilder sb = new(200);
        sb.AppendFormat("SELECT ");
        sb.AppendColumnNames(properties, includeVectors: options.IncludeVectors);
        sb.AppendLine(",");
        sb.AppendFormat("VECTOR_DISTANCE('{0}', {1}, CAST(@vector AS VECTOR({2}))) AS [score]",
            distanceMetric, GetColumnName(vectorProperty), vector.Length);
        sb.AppendLine();
        sb.Append("FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendLine();
        if (options.Filter is not null)
        {
            int startParamIndex = command.Parameters.Count;

            SqlServerFilterTranslator translator = new(storagePropertyNamesMap, options.Filter, sb, startParamIndex: startParamIndex);
            translator.Translate(appendWhere: true);
            List<object> parameters = translator.ParameterValues;

            foreach (object parameter in parameters)
            {
                command.AddParameter(vectorProperty, $"@_{startParamIndex++}", parameter);
            }
            sb.AppendLine();
        }
        sb.AppendFormat("ORDER BY [score] {0}", sorting);
        sb.AppendLine();
        // Negative Skip and Top values are rejected by the VectorSearchOptions property setters.
        // 0 is a legal value for OFFSET.
        sb.AppendFormat("OFFSET {0} ROWS FETCH NEXT {1} ROWS ONLY;", options.Skip, options.Top);

        command.CommandText = sb.ToString();
        return command;
    }

    internal static string GetColumnName(VectorStoreRecordProperty property)
        => property.StoragePropertyName ?? property.DataModelPropertyName;

    internal static StringBuilder AppendParameterName(this StringBuilder sb, VectorStoreRecordProperty property, ref int paramIndex, out string parameterName)
    {
        // In SQL Server, parameter names cannot be just a number like "@1".
        // Parameter names must start with an alphabetic character or an underscore
        // and can be followed by alphanumeric characters or underscores.
        // Since we can't guarantee that the value returned by StoragePropertyName and DataModelPropertyName
        // is valid parameter name (it can contain whitespaces, or start with a number),
        // we just append the ASCII letters, stop on the first non-ASCII letter
        // and append the index.
        string columnName = GetColumnName(property);
        int index = sb.Length;
        sb.Append('@');
        foreach (char character in columnName)
        {
            // We don't call APIs like char.IsWhitespace as they are expensive
            // as they need to handle all Unicode characters.
            if (!((character is >= 'a' and <= 'z') || (character is >= 'A' and <= 'Z')))
            {
                break;
            }
            sb.Append(character);
        }
        // In case the column name is empty or does not start with ASCII letters,
        // we provide the underscore as a prefix (allowed).
        sb.Append('_');
        // To ensure the generated parameter id is unique, we append the index.
        sb.Append(paramIndex++);
        parameterName = sb.ToString(index, sb.Length - index);

        return sb;
    }

    internal static StringBuilder AppendTableName(this StringBuilder sb, string? schema, string tableName)
    {
        // If the column name contains a ], then escape it by doubling it.
        // "Name with [brackets]" becomes [Name with [brackets]]].

        sb.Append('[');
        int index = sb.Length; // store the index, so we replace ] only for the appended part

        if (!string.IsNullOrEmpty(schema))
        {
            sb.Append(schema);
            sb.Replace("]", "]]", index, schema.Length); // replace the ] for schema
            sb.Append("].[");
            index = sb.Length;
        }

        sb.Append(tableName);
        sb.Replace("]", "]]", index, tableName.Length);
        sb.Append(']');

        return sb;
    }

    private static StringBuilder AppendColumnNames(this StringBuilder sb,
        IEnumerable<VectorStoreRecordProperty> properties,
        string? prefix = null,
        bool includeVectors = true)
    {
        bool any = false;
        foreach (VectorStoreRecordProperty property in properties)
        {
            if (!includeVectors && property is VectorStoreRecordVectorProperty)
            {
                continue;
            }

            if (prefix is not null)
            {
                sb.Append(prefix);
            }
            // Use square brackets to escape column names.
            sb.AppendFormat("[{0}],", GetColumnName(property));
            any = true;
        }

        if (any)
        {
            --sb.Length; // remove the last comma
        }

        return sb;
    }

    private static StringBuilder AppendKeyParameterList<TKey>(this StringBuilder sb,
        IEnumerable<TKey> keys, SqlCommand command, VectorStoreRecordKeyProperty keyProperty, out bool emptyKeys)
    {
        int keyIndex = 0;
        foreach (TKey key in keys)
        {
            // The caller ensures that keys collection is not null.
            // We need to ensure that none of the keys is null.
            Verify.NotNull(key);

            sb.AppendParameterName(keyProperty, ref keyIndex, out string keyParamName);
            sb.Append(',');
            command.AddParameter(keyProperty, keyParamName, key);
        }

        emptyKeys = keyIndex == 0;
        sb.Length--; // remove the last comma
        return sb;
    }

    private static SqlCommand CreateCommand(this SqlConnection connection, StringBuilder sb)
    {
        SqlCommand command = connection.CreateCommand();
        command.CommandText = sb.ToString();
        return command;
    }

    private static void AddParameter(this SqlCommand command, VectorStoreRecordProperty property, string name, object? value)
    {
        switch (value)
        {
            case null when property.PropertyType == typeof(byte[]):
                command.Parameters.Add(name, System.Data.SqlDbType.VarBinary).Value = DBNull.Value;
                break;
            case null:
            case ReadOnlyMemory<float> vector when vector.Length == 0:
                command.Parameters.AddWithValue(name, DBNull.Value);
                break;
            case byte[] buffer:
                command.Parameters.Add(name, System.Data.SqlDbType.VarBinary).Value = buffer;
                break;
            case ReadOnlyMemory<float> vector:
                command.Parameters.AddWithValue(name, JsonSerializer.Serialize(vector));
                break;
            default:
                command.Parameters.AddWithValue(name, value);
                break;
        }
    }

    private static (string sqlName, string? autoGenerate) Map(Type type)
    {
        return type switch
        {
            Type t when t == typeof(byte) => ("TINYINT", null),
            Type t when t == typeof(short) => ("SMALLINT", null),
            Type t when t == typeof(int) => ("INT", "IDENTITY(1,1)"),
            Type t when t == typeof(long) => ("BIGINT", "IDENTITY(1,1)"),
            Type t when t == typeof(Guid) => ("UNIQUEIDENTIFIER", "DEFAULT NEWSEQUENTIALID()"),
            Type t when t == typeof(string) => ("NVARCHAR(255)", null),
            Type t when t == typeof(byte[]) => ("VARBINARY(MAX)", null),
            Type t when t == typeof(bool) => ("BIT", null),
            Type t when t == typeof(DateTime) => ("DATETIME2", null),
#if NET
            Type t when t == typeof(TimeOnly) => ("TIME", null),
#endif
            Type t when t == typeof(decimal) => ("DECIMAL", null),
            Type t when t == typeof(double) => ("FLOAT", null),
            Type t when t == typeof(float) => ("REAL", null),
            _ => throw new NotSupportedException($"Type {type} is not supported.")
        };
    }

    // Source: https://learn.microsoft.com/sql/t-sql/functions/vector-distance-transact-sql
    private static (string distanceMetric, string sorting) MapDistanceFunction(string name) => name switch
    {
        // A value of 0 indicates that the vectors are identical in direction (cosine similarity of 1),
        // while a value of 1 indicates that the vectors are orthogonal (cosine similarity of 0).
        DistanceFunction.CosineDistance => ("COSINE", "ASC"),
        // A value of 0 indicates that the vectors are identical, while larger values indicate greater dissimilarity.
        DistanceFunction.EuclideanDistance => ("EUCLIDEAN", "ASC"),
        // A value closer to 0 indicates higher similarity, while more negative values indicate greater dissimilarity.
        DistanceFunction.NegativeDotProductSimilarity => ("DOT", "DESC"),
        _ => throw new NotSupportedException($"Distance function {name} is not supported.")
    };
}
