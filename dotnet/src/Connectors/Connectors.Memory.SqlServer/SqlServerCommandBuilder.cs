// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq.Expressions;
using System.Text;
using System.Text.Json;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

#pragma warning disable CA2100 // Review SQL queries for security vulnerabilities

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal static class SqlServerCommandBuilder
{
    internal static SqlCommand CreateTable(
        SqlConnection connection,
        string? schema,
        string tableName,
        bool ifNotExists,
        VectorStoreRecordModel model)
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
        sb.AppendFormat("[{0}] {1} NOT NULL,", model.KeyProperty.StorageName, Map(model.KeyProperty));
        sb.AppendLine();

        foreach (var property in model.DataProperties)
        {
            sb.AppendFormat("[{0}] {1},", property.StorageName, Map(property));
            sb.AppendLine();
        }

        foreach (var property in model.VectorProperties)
        {
            sb.AppendFormat("[{0}] VECTOR({1}),", property.StorageName, property.Dimensions);
            sb.AppendLine();
        }

        sb.AppendFormat("PRIMARY KEY ([{0}])", model.KeyProperty.StorageName);
        sb.AppendLine();
        sb.AppendLine(");"); // end the table definition

        foreach (var dataProperty in model.DataProperties)
        {
            if (dataProperty.IsIndexed)
            {
                sb.AppendFormat("CREATE INDEX ");
                sb.AppendIndexName(tableName, dataProperty.StorageName);
                sb.AppendFormat(" ON ").AppendTableName(schema, tableName);
                sb.AppendFormat("([{0}]);", dataProperty.StorageName);
                sb.AppendLine();
            }
        }

        foreach (var vectorProperty in model.VectorProperties)
        {
            switch (vectorProperty.IndexKind)
            {
                case IndexKind.Flat or null or "": // TODO: Move to early validation
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
        VectorStoreRecordModel model,
        IDictionary<string, object?> record)
    {
        SqlCommand command = connection.CreateCommand();
        StringBuilder sb = new(200);
        sb.Append("MERGE INTO ");
        sb.AppendTableName(schema, tableName);
        sb.AppendLine(" AS t");
        sb.Append("USING (VALUES (");
        int paramIndex = 0;

        foreach (var property in model.Properties)
        {
            sb.AppendParameterName(property, ref paramIndex, out string paramName).Append(',');
            command.AddParameter(property, paramName, record[property.StorageName]);
        }

        sb[sb.Length - 1] = ')'; // replace the last comma with a closing parenthesis
        sb.Append(") AS s (");
        sb.AppendColumnNames(model.Properties);
        sb.AppendLine(")");
        sb.AppendFormat("ON (t.[{0}] = s.[{0}])", model.KeyProperty.StorageName).AppendLine();
        sb.AppendLine("WHEN MATCHED THEN");
        sb.Append("UPDATE SET ");
        foreach (var property in model.Properties)
        {
            if (property is not VectorStoreRecordKeyPropertyModel) // don't update the key
            {
                sb.AppendFormat("t.[{0}] = s.[{0}],", property.StorageName);
            }
        }
        --sb.Length; // remove the last comma
        sb.AppendLine();

        sb.Append("WHEN NOT MATCHED THEN");
        sb.AppendLine();
        sb.Append("INSERT (");
        sb.AppendColumnNames(model.Properties);
        sb.AppendLine(")");
        sb.Append("VALUES (");
        sb.AppendColumnNames(model.Properties, prefix: "s.");
        sb.AppendLine(")");
        sb.AppendFormat("OUTPUT inserted.[{0}];", model.KeyProperty.StorageName);

        command.CommandText = sb.ToString();
        return command;
    }

    internal static bool MergeIntoMany(
        SqlCommand command,
        string? schema,
        string tableName,
        VectorStoreRecordModel model,
        IEnumerable<IDictionary<string, object?>> records)
    {
        StringBuilder sb = new(200);
        // The DECLARE statement creates a table variable to store the keys of the inserted rows.
        sb.AppendFormat("DECLARE @InsertedKeys TABLE (KeyColumn {0});", Map(model.KeyProperty));
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
            foreach (var property in model.Properties)
            {
                sb.AppendParameterName(property, ref paramIndex, out string paramName).Append(',');
                command.AddParameter(property, paramName, record[property.StorageName]);
            }
            sb[sb.Length - 1] = ')'; // replace the last comma with a closing parenthesis
            sb.AppendLine(",");
            rowIndex++;
        }

        if (rowIndex == 0)
        {
            return false; // there is nothing to do!
        }

        sb.Length -= (1 + Environment.NewLine.Length); // remove the last comma and newline

        sb.Append(") AS s ("); // s stands for source
        sb.AppendColumnNames(model.Properties);
        sb.AppendLine(")");
        sb.AppendFormat("ON (t.[{0}] = s.[{0}])", model.KeyProperty.StorageName).AppendLine();
        sb.AppendLine("WHEN MATCHED THEN");
        sb.Append("UPDATE SET ");
        foreach (var property in model.Properties)
        {
            if (property is not VectorStoreRecordKeyPropertyModel) // don't update the key
            {
                sb.AppendFormat("t.[{0}] = s.[{0}],", property.StorageName);
            }
        }
        --sb.Length; // remove the last comma
        sb.AppendLine();
        sb.Append("WHEN NOT MATCHED THEN");
        sb.AppendLine();
        sb.Append("INSERT (");
        sb.AppendColumnNames(model.Properties);
        sb.AppendLine(")");
        sb.Append("VALUES (");
        sb.AppendColumnNames(model.Properties, prefix: "s.");
        sb.AppendLine(")");
        sb.AppendFormat("OUTPUT inserted.[{0}] INTO @InsertedKeys (KeyColumn);", model.KeyProperty.StorageName);
        sb.AppendLine();

        // The SELECT statement returns the keys of the inserted rows.
        sb.Append("SELECT KeyColumn FROM @InsertedKeys;");

        command.CommandText = sb.ToString();
        return true;
    }

    internal static SqlCommand DeleteSingle(
        SqlConnection connection, string? schema, string tableName,
        VectorStoreRecordKeyPropertyModel keyProperty, object key)
    {
        SqlCommand command = connection.CreateCommand();

        int paramIndex = 0;
        StringBuilder sb = new(100);
        sb.Append("DELETE FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendFormat(" WHERE [{0}] = ", keyProperty.StorageName);
        sb.AppendParameterName(keyProperty, ref paramIndex, out string keyParamName);
        command.AddParameter(keyProperty, keyParamName, key);

        command.CommandText = sb.ToString();
        return command;
    }

    internal static bool DeleteMany<TKey>(
        SqlCommand command, string? schema, string tableName,
        VectorStoreRecordKeyPropertyModel keyProperty, IEnumerable<TKey> keys)
    {
        StringBuilder sb = new(100);
        sb.Append("DELETE FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendFormat(" WHERE [{0}] IN (", keyProperty.StorageName);
        sb.AppendKeyParameterList(keys, command, keyProperty, out bool emptyKeys);
        sb.Append(')'); // close the IN clause

        if (emptyKeys)
        {
            return false;
        }

        command.CommandText = sb.ToString();
        return true;
    }

    internal static SqlCommand SelectSingle(
        SqlConnection sqlConnection, string? schema, string collectionName,
        VectorStoreRecordModel model,
        object key,
        bool includeVectors)
    {
        SqlCommand command = sqlConnection.CreateCommand();

        int paramIndex = 0;
        StringBuilder sb = new(200);
        sb.AppendFormat("SELECT ");
        sb.AppendColumnNames(model.Properties, includeVectors: includeVectors);
        sb.AppendLine();
        sb.Append("FROM ");
        sb.AppendTableName(schema, collectionName);
        sb.AppendLine();
        sb.AppendFormat("WHERE [{0}] = ", model.KeyProperty.StorageName);
        sb.AppendParameterName(model.KeyProperty, ref paramIndex, out string keyParamName);
        command.AddParameter(model.KeyProperty, keyParamName, key);

        command.CommandText = sb.ToString();
        return command;
    }

    internal static bool SelectMany<TKey>(
        SqlCommand command, string? schema, string tableName,
        VectorStoreRecordModel model,
        IEnumerable<TKey> keys,
        bool includeVectors)
    {
        StringBuilder sb = new(200);
        sb.AppendFormat("SELECT ");
        sb.AppendColumnNames(model.Properties, includeVectors: includeVectors);
        sb.AppendLine();
        sb.Append("FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendLine();
        sb.AppendFormat("WHERE [{0}] IN (", model.KeyProperty.StorageName);
        sb.AppendKeyParameterList(keys, command, model.KeyProperty, out bool emptyKeys);
        sb.Append(')'); // close the IN clause

        if (emptyKeys)
        {
            return false; // there is nothing to do!
        }

        command.CommandText = sb.ToString();
        return true;
    }

    internal static SqlCommand SelectVector<TRecord>(
        SqlConnection connection, string? schema, string tableName,
        VectorStoreRecordVectorPropertyModel vectorProperty,
        VectorStoreRecordModel model,
        int top,
        VectorSearchOptions<TRecord> options,
        ReadOnlyMemory<float> vector)
    {
        string distanceFunction = vectorProperty.DistanceFunction ?? DistanceFunction.CosineDistance;
        (string distanceMetric, string sorting) = MapDistanceFunction(distanceFunction);

        SqlCommand command = connection.CreateCommand();
        command.Parameters.AddWithValue("@vector", JsonSerializer.Serialize(vector));

        StringBuilder sb = new(200);
        sb.AppendFormat("SELECT ");
        sb.AppendColumnNames(model.Properties, includeVectors: options.IncludeVectors);
        sb.AppendLine(",");
        sb.AppendFormat("VECTOR_DISTANCE('{0}', {1}, CAST(@vector AS VECTOR({2}))) AS [score]",
            distanceMetric, vectorProperty.StorageName, vector.Length);
        sb.AppendLine();
        sb.Append("FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendLine();
        if (options.Filter is not null)
        {
            int startParamIndex = command.Parameters.Count;

            SqlServerFilterTranslator translator = new(model, options.Filter, sb, startParamIndex: startParamIndex);
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
        sb.AppendFormat("OFFSET {0} ROWS FETCH NEXT {1} ROWS ONLY;", options.Skip, top);

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand SelectWhere<TRecord>(
        Expression<Func<TRecord, bool>> filter,
        int top,
        GetFilteredRecordOptions<TRecord> options,
        SqlConnection connection, string? schema, string tableName,
        VectorStoreRecordModel model)
    {
        SqlCommand command = connection.CreateCommand();

        StringBuilder sb = new(200);
        sb.AppendFormat("SELECT ");
        sb.AppendColumnNames(model.Properties, includeVectors: options.IncludeVectors);
        sb.AppendLine();
        sb.Append("FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendLine();
        if (filter is not null)
        {
            int startParamIndex = command.Parameters.Count;

            SqlServerFilterTranslator translator = new(model, filter, sb, startParamIndex: startParamIndex);
            translator.Translate(appendWhere: true);
            List<object> parameters = translator.ParameterValues;

            foreach (object parameter in parameters)
            {
                command.AddParameter(property: null, $"@_{startParamIndex++}", parameter);
            }
            sb.AppendLine();
        }

        if (options.OrderBy.Values.Count > 0)
        {
            sb.Append("ORDER BY ");

            foreach (var sortInfo in options.OrderBy.Values)
            {
                sb.AppendFormat("[{0}] {1},",
                    model.GetDataOrKeyProperty(sortInfo.PropertySelector).StorageName,
                    sortInfo.Ascending ? "ASC" : "DESC");
            }

            sb.Length--; // remove the last comma
            sb.AppendLine();
        }
        else
        {
            // no order by properties, but we need to add something for OFFSET and NEXT to work
            sb.AppendLine("ORDER BY (SELECT 1)");
        }

        // Negative Skip and Top values are rejected by the GetFilteredRecordOptions property setters.
        // 0 is a legal value for OFFSET.
        sb.AppendFormat("OFFSET {0} ROWS FETCH NEXT {1} ROWS ONLY;", options.Skip, top);

        command.CommandText = sb.ToString();
        return command;
    }

    internal static StringBuilder AppendParameterName(this StringBuilder sb, VectorStoreRecordPropertyModel property, ref int paramIndex, out string parameterName)
    {
        // In SQL Server, parameter names cannot be just a number like "@1".
        // Parameter names must start with an alphabetic character or an underscore
        // and can be followed by alphanumeric characters or underscores.
        // Since we can't guarantee that the value returned by StoragePropertyName and DataModelPropertyName
        // is valid parameter name (it can contain whitespaces, or start with a number),
        // we just append the ASCII letters, stop on the first non-ASCII letter
        // and append the index.
        int index = sb.Length;
        sb.Append('@');
        foreach (char character in property.StorageName)
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
            sb.Replace("]", "]]", index, schema!.Length); // replace the ] for schema
            sb.Append("].[");
            index = sb.Length;
        }

        sb.Append(tableName);
        sb.Replace("]", "]]", index, tableName.Length);
        sb.Append(']');

        return sb;
    }

    private static StringBuilder AppendColumnNames(this StringBuilder sb,
        IEnumerable<VectorStoreRecordPropertyModel> properties,
        string? prefix = null,
        bool includeVectors = true)
    {
        bool any = false;
        foreach (var property in properties)
        {
            if (!includeVectors && property is VectorStoreRecordVectorPropertyModel)
            {
                continue;
            }

            if (prefix is not null)
            {
                sb.Append(prefix);
            }
            // Use square brackets to escape column names.
            sb.AppendFormat("[{0}],", property.StorageName);
            any = true;
        }

        if (any)
        {
            --sb.Length; // remove the last comma
        }

        return sb;
    }

    private static StringBuilder AppendKeyParameterList<TKey>(this StringBuilder sb,
        IEnumerable<TKey> keys, SqlCommand command, VectorStoreRecordKeyPropertyModel keyProperty, out bool emptyKeys)
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

    private static StringBuilder AppendIndexName(this StringBuilder sb, string tableName, string columnName)
    {
        int length = sb.Length;

        // "Index names must start with a letter or an underscore (_)."
        sb.Append("index");
        sb.Append('_');
        AppendAllowedOnly(tableName);
        sb.Append('_');
        AppendAllowedOnly(columnName);

        if (sb.Length > length + SqlServerConstants.MaxIndexNameLength)
        {
            sb.Length = length + SqlServerConstants.MaxIndexNameLength;
        }

        return sb;

        void AppendAllowedOnly(string value)
        {
            foreach (char c in value)
            {
                // Index names can include letters, numbers, and underscores.
                if (char.IsLetterOrDigit(c) || c == '_')
                {
                    sb.Append(c);
                }
            }
        }
    }

    private static SqlCommand CreateCommand(this SqlConnection connection, StringBuilder sb)
    {
        SqlCommand command = connection.CreateCommand();
        command.CommandText = sb.ToString();
        return command;
    }

    private static void AddParameter(this SqlCommand command, VectorStoreRecordPropertyModel? property, string name, object? value)
    {
        switch (value)
        {
            case null when property?.Type == typeof(byte[]):
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

    private static string Map(VectorStoreRecordPropertyModel property) => property.Type switch
    {
        Type t when t == typeof(byte) => "TINYINT",
        Type t when t == typeof(short) => "SMALLINT",
        Type t when t == typeof(int) => "INT",
        Type t when t == typeof(long) => "BIGINT",
        Type t when t == typeof(Guid) => "UNIQUEIDENTIFIER",
        Type t when t == typeof(string) && property is VectorStoreRecordKeyPropertyModel => "NVARCHAR(4000)",
        Type t when t == typeof(string) && property is VectorStoreRecordDataPropertyModel { IsIndexed: true } => "NVARCHAR(4000)",
        Type t when t == typeof(string) => "NVARCHAR(MAX)",
        Type t when t == typeof(byte[]) => "VARBINARY(MAX)",
        Type t when t == typeof(bool) => "BIT",
        Type t when t == typeof(DateTime) => "DATETIME2",
#if NET
        Type t when t == typeof(TimeOnly) => "TIME",
#endif
        Type t when t == typeof(decimal) => "DECIMAL",
        Type t when t == typeof(double) => "FLOAT",
        Type t when t == typeof(float) => "REAL",
        _ => throw new NotSupportedException($"Type {property.Type} is not supported.")
    };

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
