using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

#pragma warning disable CA2100 // Review SQL queries for security vulnerabilities

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

        static string GetColumnName(VectorStoreRecordProperty property) => property.StoragePropertyName ?? property.DataModelPropertyName;

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
}
