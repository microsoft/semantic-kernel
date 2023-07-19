// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Harness;

using System;
using System.Collections.Generic;
using System.Data;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using SemanticKernel.Data.Nl2Sql.Library.Schema;

internal sealed class SqlSchemaProvider
{
    private readonly SqlConnection connection;

    public SqlSchemaProvider(SqlConnection connection)
    {
        this.connection = connection;
    }

    public async Task<SchemaDefinition> GetSchemaAsync(string? description, params string[] tableNames)
    {
        var tableFilter = new HashSet<string>(tableNames ?? Array.Empty<string>(), StringComparer.OrdinalIgnoreCase);

        var tables =
            await this.QueryTablesAsync()
                .Where(t => tableFilter.Count == 0 || tableFilter.Contains(t.Name))
                .ToArrayAsync()
                .ConfigureAwait(false);

        return new SchemaDefinition(this.connection.Database, description, tables);
    }

    private async IAsyncEnumerable<SchemaTable> QueryTablesAsync()
    {
        var columnMap = new Dictionary<string, LinkedList<SchemaColumn>>(StringComparer.InvariantCultureIgnoreCase);
        var viewMap = new HashSet<string>(StringComparer.InvariantCultureIgnoreCase);
        var keyMap = await this.QueryReferencesAsync().ConfigureAwait(false);
        var tableDescription = await this.QueryTableDescriptionsAsync().ConfigureAwait(false);

        using var reader = await this.ExecuteQueryAsync(Statements.DescribeColumns).ConfigureAwait(false);
        while (await reader.ReadAsync().ConfigureAwait(false))
        {
            var schemaName = reader.GetString(Statements.Columns.SchemaName);
            var tableName = reader.GetString(Statements.Columns.TableName);
            var fullName = FormatName(schemaName, tableName);

            if (!columnMap.TryGetValue(fullName, out var columns))
            {
                columns = new LinkedList<SchemaColumn>();
                columnMap[fullName] = columns;
            }

            var columnName = reader.GetString(Statements.Columns.ColumnName);
            var columnDesc = reader.IsDBNull(Statements.Columns.ColumnDesc) ? null : reader.GetString(Statements.Columns.ColumnDesc);
            var columnType = reader.GetString(Statements.Columns.ColumnType);
            var isPk = reader.GetBoolean(Statements.Columns.IsPK);

            if (reader.GetBoolean(Statements.Columns.IsView))
            {
                viewMap.Add(fullName);
            }

            keyMap.TryGetValue(FormatName(schemaName, tableName, columnName), out var reference);

            columns.AddLast(new SchemaColumn(columnName, columnDesc, columnType, isPk, reference.table, reference.column));
        }

        foreach (var kvp in columnMap)
        {
            tableDescription.TryGetValue(kvp.Key, out var description);
            yield return new SchemaTable(kvp.Key, description, viewMap.Contains(kvp.Key), kvp.Value.ToArray());
        }
    }

    private async Task<Dictionary<string, (string table, string column)>> QueryReferencesAsync()
    {
        var keyMap = new Dictionary<string, (string table, string column)>(StringComparer.OrdinalIgnoreCase);

        using var reader = await this.ExecuteQueryAsync(Statements.DescribeReferences).ConfigureAwait(false);

        while (await reader.ReadAsync().ConfigureAwait(false))
        {
            var schemaName = reader.GetString(Statements.Columns.SchemaName);
            var tableName = reader.GetString(Statements.Columns.TableName);
            var columnName = reader.GetString(Statements.Columns.ColumnName);
            var tableRefName = reader.GetString(Statements.Columns.ReferencedTableName);
            var columnRefName = reader.GetString(Statements.Columns.ReferencedColumnName);

            keyMap.Add(FormatName(schemaName, tableName, columnName), (FormatName(schemaName, tableRefName), columnRefName));
        }

        return keyMap;
    }

    private async Task<Dictionary<string, string?>> QueryTableDescriptionsAsync()
    {
        var tableMap = new Dictionary<string, string?>(StringComparer.OrdinalIgnoreCase);

        using var reader = await this.ExecuteQueryAsync(Statements.DescribeTables).ConfigureAwait(false);

        while (await reader.ReadAsync().ConfigureAwait(false))
        {
            var schemaName = reader.GetString(Statements.Columns.SchemaName);
            var tableName = reader.GetString(Statements.Columns.TableName);
            var tableDesc = reader.IsDBNull(Statements.Columns.TableDesc) ? null : reader.GetString(Statements.Columns.TableDesc);

            tableMap.Add(FormatName(schemaName, tableName), tableDesc);
        }

        return tableMap;
    }

    private async Task<SqlDataReader> ExecuteQueryAsync(string statement)
    {
        using var cmd = this.connection.CreateCommand();

        cmd.CommandText = statement;

        return await cmd.ExecuteReaderAsync().ConfigureAwait(false);
    }

    public static string FormatName(params string[] parts)
    {
        return string.Join(CultureInfo.InvariantCulture.NumberFormat.NumberDecimalSeparator, parts);
    }

    private static class Statements
    {
        public static class Columns
        {
            public const string SchemaName = nameof(SchemaName);
            public const string TableName = nameof(TableName);
            public const string TableDesc = nameof(TableDesc);
            public const string ColumnName = nameof(ColumnName);
            public const string ColumnDesc = nameof(ColumnDesc);
            public const string ColumnType = nameof(ColumnType);
            public const string IsPK = nameof(IsPK);
            public const string IsView = nameof(IsView);
            public const string ReferencedTableName = nameof(ReferencedTableName);
            public const string ReferencedColumnName = nameof(ReferencedColumnName);
        }

        public const string DescribeTables =
@"SELECT 
  S.name AS SchemaName,
  O.name AS TableName,
  ep.value AS TableDesc
FROM sys.extended_properties EP
JOIN sys.tables O ON ep.major_id = O.object_id
JOIN sys.schemas S on O.schema_id = S.schema_id
WHERE ep.name = 'MS_DESCRIPTION'
AND ep.minor_id = 0";

        public const string DescribeColumns =
@"SELECT
    sch.name AS SchemaName,
    tab.name AS TableName,
    col.name AS ColumnName,
	ep.value AS ColumnDesc,
    base.name AS ColumnType,
    CAST(IIF(ic.column_id IS NULL, 0, 1) AS bit) IsPK,
    tab.IsView
FROM 
(
    select object_id, schema_id, name, CAST(0 as bit) IsView from sys.tables
    UNION ALL
    select object_id, schema_id, name, CAST(1 as bit) IsView from sys.views
) tab
INNER JOIN sys.objects obj ON obj.object_id = tab.object_id
INNER JOIN sys.schemas sch ON tab.schema_id = sch.schema_id
INNER JOIN sys.columns col ON col.object_id = tab.object_id
INNER JOIN sys.types t ON col.user_type_id = t.user_type_id
INNER JOIN sys.types base ON t.system_type_id = base.user_type_id
LEFT OUTER JOIN sys.indexes pk ON tab.object_id = pk.object_id AND pk.is_primary_key = 1
LEFT OUTER JOIN sys.index_columns ic ON ic.object_id = pk.object_id AND ic.index_id = pk.index_id AND ic.column_id = col.column_id 
LEFT OUTER JOIN sys.extended_properties ep ON ep.major_id = col.object_id AND ep.minor_id = col.column_id and ep.name = 'MS_DESCRIPTION'
WHERE sch.name != 'sys'
ORDER BY SchemaName, TableName, IsPK DESC, ColumnName";

        public const string DescribeReferences =
@"SELECT
    obj.name AS KeyName,
    sch.name AS SchemaName,
    parentTab.name AS TableName,
    parentCol.name AS ColumnName,
    refTable.name AS ReferencedTableName,
    refCol.name AS ReferencedColumnName
  FROM sys.foreign_key_columns fkc
  INNER JOIN sys.objects obj ON obj.object_id = fkc.constraint_object_id
  INNER JOIN sys.tables parentTab ON parentTab.object_id = fkc.parent_object_id
  INNER JOIN sys.schemas sch ON parentTab.schema_id = sch.schema_id
  INNER JOIN sys.columns parentCol ON parentCol.column_id = parent_column_id AND parentCol.object_id = parentTab.object_id
  INNER JOIN sys.tables refTable ON refTable.object_id = fkc.referenced_object_id
  INNER JOIN sys.columns refCol ON refCol.column_id = referenced_column_id AND refCol.object_id = refTable.object_id";
    }
}
