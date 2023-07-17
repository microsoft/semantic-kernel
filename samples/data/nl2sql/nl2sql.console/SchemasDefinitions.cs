// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql;

using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using SemanticKernel.Data.Nl2Sql.Schema;

/// <summary>
/// Defines the schemas initialized by the console.
/// </summary>
internal static class SchemasDefinitions
{
    /// <summary>
    /// Enumerates the <see cref="SchemaDefinition"/> known to the console.
    /// </summary>
    /// <remarks>
    /// After testing with the sample data-sources, try one of your own!
    /// </remarks>
    public static async IAsyncEnumerable<SchemaDefinition> GetSchemasAsync()
    {
        yield return await GetSchemaAsync("adventureworkslt").ConfigureAwait(false);
        yield return await GetSchemaAsync("descriptiontest").ConfigureAwait(false);
        // TODO: Load your own schema here (comment-out others for focused exploration)
    }

    /// <summary>
    /// Helper method to load schema.json
    /// </summary>
    private static async Task<SchemaDefinition> GetSchemaAsync(string schemaName)
    {
        var filePath = Path.Combine(Repo.RootConfig, "schemas", $"{schemaName}.json");

        return await SchemaSerializer.ReadAsync(filePath).ConfigureAwait(false);
    }
}
