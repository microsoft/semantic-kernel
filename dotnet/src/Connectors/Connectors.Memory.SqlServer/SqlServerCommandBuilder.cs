using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.NetworkInformation;
using System.Text;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

#pragma warning disable CA2100 // Review SQL queries for security vulnerabilities
#pragma warning disable CA1851 // Possible multiple enumerations of IEnumerable

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal static class SqlServerCommandBuilder
{
    internal static SqlCommand CreateTable(
        SqlConnection connection,
        SqlServerVectorStoreOptions options,
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
            sb.AppendTableName(options.Schema, tableName);
            sb.AppendLine("', N'U') IS NULL");
        }
        sb.Append("CREATE TABLE ");
        sb.AppendTableName(options.Schema, tableName);
        sb.AppendLine(" (");
        // Use square brackets to escape column names.
        string keyColumnName = GetColumnName(keyProperty);
        sb.AppendFormat("[{0}] {1} NOT NULL,", keyColumnName, Map(keyProperty.PropertyType).sqlName);
        sb.AppendLine();
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
        sb.AppendFormat("PRIMARY KEY NONCLUSTERED ([{0}])", keyColumnName);
        sb.AppendLine();
        sb.Append(')'); // end the table definition

        return connection.CreateCommand(sb);
    }

    internal static SqlCommand DropTable(SqlConnection connection, string schema, string tableName)
    {
        StringBuilder sb = new(50);
        sb.Append("DROP TABLE IF EXISTS ");
        sb.AppendTableName(schema, tableName);

        return connection.CreateCommand(sb);
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

        StringBuilder sb = new(200);
        sb.Append("INSERT INTO ");
        sb.AppendTableName(options.Schema, tableName);
        sb.Append(" (");
        var nonKeyProperties = dataProperties.Concat<VectorStoreRecordProperty>(vectorProperties);
        sb.AppendColumnNames(nonKeyProperties);
        sb.AppendLine(")");
        sb.AppendFormat("OUTPUT inserted.[{0}]", GetColumnName(keyProperty));
        sb.AppendLine();
        sb.Append("VALUES (");
        foreach (VectorStoreRecordProperty property in nonKeyProperties)
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

    internal static SqlCommand MergeIntoSingle(
        SqlConnection connection,
        SqlServerVectorStoreOptions options,
        string tableName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordProperty> properties,
        Dictionary<string, object?> record)
    {
        SqlCommand command = connection.CreateCommand();
        StringBuilder sb = new(200);
        sb.Append("MERGE INTO ");
        sb.AppendTableName(options.Schema, tableName);
        sb.AppendLine(" AS t");
        sb.Append("USING (VALUES (");
        foreach (VectorStoreRecordProperty property in properties)
        {
            int index = sb.Length;
            sb.AppendFormat("@{0},", GetColumnName(property));
            string paramName = sb.ToString(index, sb.Length - index - 1); // 1 is for the comma
            command.Parameters.AddWithValue(paramName, record[property.DataModelPropertyName] ?? (object)DBNull.Value);
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
        sb.Append(");");

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand MergeIntoMany(
        SqlConnection connection,
        SqlServerVectorStoreOptions options,
        string tableName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordProperty> properties,
        IEnumerable<Dictionary<string, object?>> records)
    {
        SqlCommand command = connection.CreateCommand();

        StringBuilder sb = new(200);
        // The DECLARE statement creates a table variable to store the keys of the inserted rows.
        sb.AppendFormat("DECLARE @InsertedKeys TABLE (KeyColumn {0});", Map(keyProperty.PropertyType).sqlName);
        sb.AppendLine();
        // The MERGE statement performs the upsert operation and outputs the keys of the inserted rows into the table variable.
        sb.Append("MERGE INTO ");
        sb.AppendTableName(options.Schema, tableName);
        sb.AppendLine(" AS t"); // t stands for target
        sb.AppendLine("USING (VALUES");
        int rowIndex = 0;
        foreach (var record in records)
        {
            sb.Append('(');
            foreach (VectorStoreRecordProperty property in properties)
            {
                int index = sb.Length;
                sb.AppendFormat("@{0}_{1},", GetColumnName(property), rowIndex);
                string paramName = sb.ToString(index, sb.Length - index - 1); // 1 is for the comma
                command.Parameters.AddWithValue(paramName, record[property.DataModelPropertyName] ?? (object)DBNull.Value);
            }
            sb[sb.Length - 1] = ')'; // replace the last comma with a closing parenthesis
            sb.AppendLine(",");
            rowIndex++;
        }

        if (rowIndex == 0)
        {
            // TODO adsitnik clarify: should we throw or simply do nothing?
            throw new ArgumentException("The value cannot be empty.", nameof(records));
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
        SqlConnection connection, string schema, string tableName,
        VectorStoreRecordKeyProperty keyProperty, object key)
    {
        SqlCommand command = connection.CreateCommand();

        string keyParamName = $"@{GetColumnName(keyProperty)}";
        command.Parameters.AddWithValue(keyParamName, key);

        StringBuilder sb = new(100);
        sb.Append("DELETE FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendFormat(" WHERE [{0}] = {1}", GetColumnName(keyProperty), keyParamName);

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand DeleteMany<TKey>(
        SqlConnection connection, string schema, string tableName,
        VectorStoreRecordKeyProperty keyProperty, IEnumerable<TKey> keys)
    {
        SqlCommand command = connection.CreateCommand();

        StringBuilder sb = new(100);
        sb.Append("DELETE FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendFormat(" WHERE [{0}] IN (", GetColumnName(keyProperty));
        sb.AppendKeyParameterList(keys, command);
        sb.Append(')'); // close the IN clause

        command.CommandText = sb.ToString();
        return command;
    }

    internal static SqlCommand SelectSingle(
        SqlConnection sqlConnection, string schema, string collectionName,
        VectorStoreRecordKeyProperty keyProperty,
        IReadOnlyList<VectorStoreRecordProperty> properties,
        object key)
    {
        SqlCommand command = sqlConnection.CreateCommand();

        string keyParamName = $"@{GetColumnName(keyProperty)}";
        command.Parameters.AddWithValue(keyParamName, key);

        StringBuilder sb = new(200);
        sb.AppendFormat("SELECT ");
        sb.AppendColumnNames(properties);
        sb.AppendLine();
        sb.Append("FROM ");
        sb.AppendTableName(schema, collectionName);
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

        StringBuilder sb = new(200);
        sb.AppendFormat("SELECT ");
        sb.AppendColumnNames(properties);
        sb.AppendLine();
        sb.Append("FROM ");
        sb.AppendTableName(schema, tableName);
        sb.AppendLine();
        sb.AppendFormat("WHERE [{0}] IN (", GetColumnName(keyProperty));
        sb.AppendKeyParameterList(keys, command);
        sb.Append(')'); // close the IN clause

        command.CommandText = sb.ToString();
        return command;
    }

    internal static string GetColumnName(VectorStoreRecordProperty property)
        => property.StoragePropertyName ?? property.DataModelPropertyName;

    internal static StringBuilder AppendTableName(this StringBuilder sb, string schema, string tableName)
    {
        // If the column name contains a ], then escape it by doubling it.
        // "Name with [brackets]" becomes [Name with [brackets]]].

        sb.Append('[');
        int index = sb.Length; // store the index, so we replace ] only for schema
        sb.Append(schema);
        sb.Replace("]", "]]", index, schema.Length); // replace the ] for schema
        sb.Append("].[");
        index = sb.Length;
        sb.Append(tableName);
        sb.Replace("]", "]]", index, tableName.Length);
        sb.Append(']');

        return sb;
    }

    private static StringBuilder AppendColumnNames(this StringBuilder sb,
        IEnumerable<VectorStoreRecordProperty> properties,
        string? prefix = null)
    {
        bool any = false;
        foreach (VectorStoreRecordProperty property in properties)
        {
            if (prefix is not null)
            {
                sb.Append(prefix);
            }
            sb.AppendFormat("[{0}],", GetColumnName(property));
            any = true;
        }

        if (any)
        {
            --sb.Length; // remove the last comma
        }

        return sb;
    }

    private static StringBuilder AppendKeyParameterList<TKey>(this StringBuilder sb, IEnumerable<TKey> keys, SqlCommand command)
    {
        int keyIndex = 0;
        foreach (TKey key in keys)
        {
            // The caller ensures that keys collection is not null.
            // We need to ensure that none of the keys is null.
            Verify.NotNull(key);
            int index = sb.Length;
            sb.AppendFormat("@k{0},", keyIndex++);
            string keyParam = sb.ToString(index, sb.Length - index - 1); // 1 is for the comma
            command.Parameters.AddWithValue(keyParam, key);
        }

        if (keyIndex == 0)
        {
            // TODO adsitnik clarify: should we throw or simply do nothing?
            throw new ArgumentException("The value cannot be empty.", nameof(keys));
        }

        sb.Length--; // remove the last comma
        return sb;
    }

    private static SqlCommand CreateCommand(this SqlConnection connection, StringBuilder sb)
    {
        SqlCommand command = connection.CreateCommand();
        command.CommandText = sb.ToString();
        return command;
    }

    private static (string sqlName, bool isNullable) Map(Type type) => type switch
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
