// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Services;

using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using SemanticKernel.Data.Nl2Sql.Schema;

/// <summary>
/// Responsible for loading the defined schemas into semantic memory.
/// </summary>
internal static class SchemaProvider
{
    public const string MemoryCollectionName = "data-schemas";

    public static async IAsyncEnumerable<string> InitializeAsync(IKernel kernel)
    {
        await foreach (var schema in GetSchemasAsync())
        {
            var schemaText = await schema.FormatAsync(YamlSchemaFormatter.Instance).ConfigureAwait(false);

            await kernel.Memory.SaveInformationAsync(MemoryCollectionName, schemaText, schema.Name).ConfigureAwait(false);

            yield return schema.Name;
        }
    }

    /// <summary>
    /// Enumerates the <see cref="SchemaDefinition"/> known to the console.
    /// </summary>
    private static async IAsyncEnumerable<SchemaDefinition> GetSchemasAsync()
    {
        foreach (var schemaName in SchemasDefinitions.GetNames())
        {
            yield return await GetSchemaAsync(schemaName).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Helper method to load schema.json
    /// </summary>
    private static async Task<SchemaDefinition> GetSchemaAsync(string schemaName)
    {
        var filePath = Path.Combine(Repo.RootConfigFolder, "schemas", $"{schemaName}.json");

        return await SchemaSerializer.ReadAsync(filePath).ConfigureAwait(false);
    }
}
