using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

#pragma warning disable CA2100 // Review SQL queries for security vulnerabilities
#pragma warning disable CA1851 // Possible multiple enumerations of IEnumerable

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal static class SqlServerCommandBuilder
{
    internal static string GetSanitizedFullTableName(string schema, string tableName)
    {
        // If the column name contains a ], then escape it by doubling it.
        // "Name with [brackets]" becomes [Name with [brackets]]].

        StringBuilder sb = new(tableName.Length + schema.Length + 5);
        sb.Append('[');
        sb.Append(schema);
        sb.Replace("]", "]]"); // replace the ] for schema
        sb.Append("].[");
        int index = sb.Length; // store the index, so we don't replace ] for schema twice
        sb.Append(tableName);
        sb.Replace("]", "]]", index, tableName.Length);
        sb.Append(']');

        return sb.ToString();
    }

    internal static SqlCommand CreateTable(
        SqlConnection connection,
        SqlServerVectorStoreOptions options,
        string tableName,
        bool ifNotExists,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordDataProperty> dataProperties,
        IReadOnlyList<VectorStoreRecordVectorProperty> vectorProperties)
    {
        SqlCommand command = connection.CreateCommand();
        string fullTableName = GetSanitizedFullTableName(options.Schema, tableName);

        StringBuilder sb = new(200);
        if (ifNotExists)
        {
            sb.AppendFormat("IF OBJECT_ID(N'{0}', N'U') IS NULL", fullTableName).AppendLine();
        }
        sb.AppendFormat("CREATE TABLE {0} (", fullTableName).AppendLine();
        // Use square brackets to escape column names.
        string keyColumnName = GetColumnName(keyProperty);
        sb.AppendFormat("[{0}] {1} NOT NULL,", keyColumnName, Map(keyProperty.PropertyType).sqlName).AppendLine();
        for (int i = 0; i < dataProperties.Count; i++)
        {
            (string sqlName, bool isNullable) = Map(dataProperties[i].PropertyType);
            sb.AppendFormat(isNullable ? "[{0}] {1}," : "[{0}] {1} NOT NULL,", GetColumnName(dataProperties[i]), sqlName);
            sb.AppendLine();
        }
        for (int i = 0; i < vectorProperties.Count; i++)
        {
            sb.AppendFormat("[{0}] VECTOR({1}),", GetColumnName(vectorProperties[i]), vectorProperties[i].Dimensions);
            sb.AppendLine();
        }
        sb.AppendFormat("PRIMARY KEY NONCLUSTERED ([{0}])", keyColumnName).AppendLine();
        sb.Append(')'); // end the table definition
        command.CommandText = sb.ToString();
        return command;

        static (string sqlName, bool isNullable) Map(Type type) => type switch
        {
            Type t when t == typeof(int) => ("INT", false),
            Type t when t == typeof(long) => ("BIGINT", false),
            Type t when t == typeof(Guid) => ("UNIQUEIDENTIFIER", false),
            Type t when t == typeof(string) => ("NVARCHAR(255) COLLATE Latin1_General_100_BIN2", true),
            Type t when t == typeof(byte[]) => ("VARBINARY(MAX)", true),
            Type t when t == typeof(bool) => ("BIT", false),
            Type t when t == typeof(DateTime) => ("DATETIME", false),
            Type t when t == typeof(TimeSpan) => ("TIME", false),
            Type t when t == typeof(decimal) => ("DECIMAL", false),
            Type t when t == typeof(double) => ("FLOAT", false),
            Type t when t == typeof(float) => ("REAL", false),
            _ => throw new NotSupportedException($"Type {type} is not supported.")
        };
    }

    internal static SqlCommand DropTable(SqlConnection connection, string schema, string tableName)
    {
        SqlCommand command = connection.CreateCommand();
        string fullTableName = GetSanitizedFullTableName(schema, tableName);
        command.CommandText = $"DROP TABLE IF EXISTS {fullTableName}";
        return command;
    }

    internal static SqlCommand SelectTableName(SqlConnection connection, string schema, string tableName)
    {
        SqlCommand command = connection.CreateCommand();
        command.CommandText = """
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                    AND TABLE_SCHEMA = @schema
                    AND TABLE_NAME = @tableName
                """;
        command.Parameters.AddWithValue("@schema", schema);
        command.Parameters.AddWithValue("@tableName", tableName); // the name is not escaped by us, just provided as parameter
        return command;
    }

    internal static SqlCommand InsertInto(
        SqlConnection connection,
        SqlServerVectorStoreOptions options,
        string tableName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordDataProperty> dataProperties,
        IReadOnlyList<VectorStoreRecordVectorProperty> vectorProperties,
        Dictionary<string, object?> record)
    {
        SqlCommand command = connection.CreateCommand();
        string fullTableName = GetSanitizedFullTableName(options.Schema, tableName);
        StringBuilder sb = new(200);
        sb.AppendFormat("INSERT INTO {0} (", fullTableName);
        // Use square brackets to escape column names.
        foreach (VectorStoreRecordProperty property in dataProperties.Concat<VectorStoreRecordProperty>(vectorProperties))
        {
            sb.AppendFormat("[{0}],", GetColumnName(property));
        }
        sb[sb.Length - 1] = ')'; // replace the last comma with a closing parenthesis
        sb.AppendLine();
        sb.AppendFormat("OUTPUT inserted.[{0}]", GetColumnName(keyProperty));
        sb.AppendLine();
        sb.Append("VALUES (");
        foreach (VectorStoreRecordProperty property in dataProperties.Concat<VectorStoreRecordProperty>(vectorProperties))
        {
            int index = sb.Length;
            sb.AppendFormat("@{0},", GetColumnName(property));
            string paramName = sb.ToString(index, sb.Length - index - 1); // 1 is for the comma
            command.Parameters.AddWithValue(paramName, record[property.DataModelPropertyName] ?? (object)DBNull.Value);
        }
        sb[sb.Length - 1] = ')'; // replace the last comma with a closing parenthesis
        sb.Append(';');

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand MergeInto(
        SqlConnection connection,
        SqlServerVectorStoreOptions options,
        string tableName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordDataProperty> dataProperties,
        IReadOnlyList<VectorStoreRecordVectorProperty> vectorProperties,
        Dictionary<string, object?> record)
    {
        SqlCommand command = connection.CreateCommand();
        string fullTableName = GetSanitizedFullTableName(options.Schema, tableName);
        StringBuilder sb = new(200);
        sb.AppendFormat("MERGE INTO {0} AS t", fullTableName).AppendLine();
        sb.Append("USING (VALUES (");
        var allProperties = new VectorStoreRecordProperty[] { keyProperty }.Concat<VectorStoreRecordProperty>(dataProperties).Concat<VectorStoreRecordProperty>(vectorProperties);
        foreach (VectorStoreRecordProperty property in allProperties)
        {
            int index = sb.Length;
            sb.AppendFormat("@{0},", GetColumnName(property));
            string paramName = sb.ToString(index, sb.Length - index - 1); // 1 is for the comma
            command.Parameters.AddWithValue(paramName, record[property.DataModelPropertyName] ?? (object)DBNull.Value);
        }
        sb[sb.Length - 1] = ')'; // replace the last comma with a closing parenthesis
        sb.AppendFormat(") AS s (");
        foreach (VectorStoreRecordProperty property in allProperties)
        {
            sb.AppendFormat("[{0}],", GetColumnName(property));
        }
        sb[sb.Length - 1] = ')'; // replace the last comma with a closing parenthesis
        sb.AppendLine();
        sb.AppendFormat("ON (t.[{0}] = s.[{0}])", GetColumnName(keyProperty)).AppendLine();
        sb.AppendLine("WHEN MATCHED THEN");
        sb.Append("UPDATE SET ");
        foreach (VectorStoreRecordProperty property in dataProperties.Concat<VectorStoreRecordProperty>(vectorProperties))
        {
            sb.AppendFormat("t.[{0}] = s.[{0}],", GetColumnName(property));
        }
        --sb.Length; // remove the last comma
        sb.AppendLine();
        sb.Append("WHEN NOT MATCHED THEN");
        sb.AppendLine();
        sb.Append("INSERT (");
        foreach (VectorStoreRecordProperty property in allProperties)
        {
            sb.AppendFormat("[{0}],", GetColumnName(property));
        }
        sb[sb.Length - 1] = ')'; // replace the last comma with a closing parenthesis
        sb.AppendLine();
        sb.Append("VALUES (");
        foreach (VectorStoreRecordProperty property in allProperties)
        {
            sb.AppendFormat("s.[{0}],", GetColumnName(property));
        }
        sb[sb.Length - 1] = ')'; // replace the last comma with a closing parenthesis
        sb.Append(';');

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand DeleteSingle(
        SqlConnection connection, string schema, string tableName,
        VectorStoreRecordKeyProperty keyProperty, object key)
    {
        SqlCommand command = connection.CreateCommand();
        string fullTableName = GetSanitizedFullTableName(schema, tableName);
        string keyParamName = $"@{GetColumnName(keyProperty)}";
        command.CommandText =
        $""""
        DELETE
        FROM {fullTableName}
        WHERE [{GetColumnName(keyProperty)}] = {keyParamName}
        """";
        command.Parameters.AddWithValue(keyParamName, key);
        return command;
    }

    internal static SqlCommand DeleteMany<TKey>(
        SqlConnection connection, string schema, string tableName,
        VectorStoreRecordKeyProperty keyProperty, IEnumerable<TKey> keys)
    {
        SqlCommand command = connection.CreateCommand();
        string fullTableName = GetSanitizedFullTableName(schema, tableName);
        StringBuilder keyParams = CreateKeyParameterList(keys, command);

        command.CommandText =
        $""""
        DELETE
        FROM {fullTableName}
        WHERE [{GetColumnName(keyProperty)}] IN ({keyParams})
        """";

        return command;
    }

    internal static SqlCommand SelectSingle(
        SqlConnection sqlConnection, string schema, string collectionName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordProperty> properties,
        object key)
    {
        SqlCommand command = sqlConnection.CreateCommand();
        string fullTableName = GetSanitizedFullTableName(schema, collectionName);
        string keyParamName = $"@{GetColumnName(keyProperty)}";
        command.Parameters.AddWithValue(keyParamName, key);

        StringBuilder sb = new(200);
        sb.AppendFormat("SELECT ");
        AppendColumnNames(properties, sb);
        sb.AppendLine();
        sb.AppendFormat("FROM {0}", fullTableName);
        sb.AppendLine();
        sb.AppendFormat("WHERE [{0}] = {1}", GetColumnName(keyProperty), keyParamName);
        command.CommandText = sb.ToString();

        return command;
    }

    internal static SqlCommand SelectMany<TKey>(
        SqlConnection connection, string schema, string tableName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordProperty> properties,
        IEnumerable<TKey> keys)
    {
        SqlCommand command = connection.CreateCommand();
        string fullTableName = GetSanitizedFullTableName(schema, tableName);
        StringBuilder keyParams = CreateKeyParameterList(keys, command);

        StringBuilder sb = new(200);
        sb.AppendFormat("SELECT ");
        AppendColumnNames(properties, sb);
        sb.AppendLine();
        sb.AppendFormat("FROM {0}", fullTableName);
        sb.AppendLine();
        sb.AppendFormat("WHERE [{0}] IN ({1})", GetColumnName(keyProperty), keyParams);

        command.CommandText = sb.ToString();

        return command;
    }

    private static void AppendColumnNames(IReadOnlyList<VectorStoreRecordProperty> properties, StringBuilder sb)
    {
        foreach (VectorStoreRecordProperty property in properties)
        {
            sb.AppendFormat("[{0}],", GetColumnName(property));
        }

        if (properties.Count > 0)
        {
            --sb.Length; // remove the last comma
        }
    }

    private static StringBuilder CreateKeyParameterList<TKey>(IEnumerable<TKey> keys, SqlCommand command)
    {
        StringBuilder keyParams = new();
        int keyIndex = 0;
        foreach (TKey key in keys)
        {
            // The caller ensures that keys collection is not null.
            // We need to ensure that none of the keys is null.
            Verify.NotNull(key);
            int index = keyParams.Length;
            keyParams.AppendFormat("@k{0},", keyIndex++);
            string keyParam = keyParams.ToString(index, keyParams.Length - index - 1); // 1 is for the comma
            command.Parameters.AddWithValue(keyParam, key);
        }

        if (keyParams.Length == 0)
        {
            // TODO adsitnik clarify: should we throw or simply do nothing?
            throw new ArgumentException("The value cannot be empty.", nameof(keys));
        }

        keyParams.Length--; // remove the last comma
        return keyParams;
    }

    internal static string GetColumnName(VectorStoreRecordProperty property)
        => property.StoragePropertyName ?? property.DataModelPropertyName;
}
