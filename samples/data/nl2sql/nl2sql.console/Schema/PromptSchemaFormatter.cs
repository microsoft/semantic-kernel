// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Schema;

using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

/// <summary>
/// Format a <see cref="SchemaDefinition"/> object.
/// </summary>
/// <example>
/// Table: stadium, columns: [*,Stadium_ID,Location,Name,Capacity,Highest,Lowest,Average]
/// Table: singer, columns: [*,Singer_ID,Name,Country,Song_Name,Song_release_year,Age,Is_male]
/// Table: concert, columns: [*,concert_ID,concert_Name,Theme,Stadium_ID,Year]
/// Table: singer_in_concert, columns: [*,concert_ID,Singer_ID]
/// Foreign_keys: [concert.Stadium_ID = stadium.Stadium_ID, singer_in_concert.concert_ID = concert.concert_ID, singer_in_concert.Singer_ID = singer.Singer_ID]
/// </example>
public sealed class PromptSchemaFormatter : ISchemaFormatter
{
    public static PromptSchemaFormatter Instance { get; } = new PromptSchemaFormatter();

    private PromptSchemaFormatter() { }

    async Task ISchemaFormatter.WriteAsync(TextWriter writer, SchemaDefinition schema)
    {
        var builder = new StringBuilder();

        foreach (var table in schema.Tables)
        {
            await writer.WriteLineAsync($"Table: {table.Name}, columns: [*,{FormatColumns(table)}]").ConfigureAwait(false);
        }

        if (builder.Length > 0)
        {
            await writer.WriteLineAsync($"Foreign_keys: [{builder}]").ConfigureAwait(false);
        }

        string FormatColumns(SchemaTable table)
        {
            return
                string.Join(
                    CultureInfo.InvariantCulture.TextInfo.ListSeparator,
                    table.Columns.Select(
                        c =>
                        {
                            if (!string.IsNullOrEmpty(c.ReferencedColumn))
                            {
                                if (builder.Length > 0)
                                {
                                    builder.Append(CultureInfo.InvariantCulture.TextInfo.ListSeparator);
                                }
                                builder.Append(CultureInfo.InvariantCulture, $"{table.Name}.{c.Name} = {c.ReferencedTable}.{c.ReferencedColumn}");
                            }

                            return c.Name;
                        }));
        }
    }
}
