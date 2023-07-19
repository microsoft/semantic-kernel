// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Library.Schema;

using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

/// <summary>
/// Format a <see cref="SchemaDefinition"/> object in YAML format.
/// </summary>
/// <remarks>
/// Turns out YAML is extremely efficient with token usage.
/// </remarks>
internal sealed class YamlSchemaFormatter : ISchemaFormatter
{
    public static YamlSchemaFormatter Instance { get; } = new YamlSchemaFormatter();

    private YamlSchemaFormatter() { }

    async Task ISchemaFormatter.WriteAsync(TextWriter writer, SchemaDefinition schema)
    {
        var builder = new StringBuilder();

        if (!string.IsNullOrWhiteSpace(schema.Description))
        {
            await writer.WriteLineAsync($"description: {schema.Description}").ConfigureAwait(false);
        }

        await writer.WriteLineAsync("tables:").ConfigureAwait(false);

        foreach (var table in schema.Tables)
        {
            await writer.WriteLineAsync($"  - {table.Name}: {table.Description}").ConfigureAwait(false);
            await writer.WriteLineAsync("    columns:").ConfigureAwait(false);

            foreach (var column in table.Columns)
            {
                await writer.WriteLineAsync($"      {column.Name}: {column.Description}").ConfigureAwait(false);
            }
        }
        await writer.WriteLineAsync("references:").ConfigureAwait(false);
        foreach (var (table, column) in schema.Tables.SelectMany(t => t.Columns.Where(c => !string.IsNullOrEmpty(c.ReferencedTable)).Select(c => (t.Name, c))))
        {
            await writer.WriteLineAsync($"  {table}.{column.Name}: {column.ReferencedTable}.{column.ReferencedColumn}").ConfigureAwait(false);
        }
    }
}
