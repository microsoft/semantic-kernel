// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Services;

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using SemanticKernel.Data.Nl2Sql.Schema;

/// <summary>
/// Responsible for loading the defined schemas into semantic memory.
/// </summary>
internal static class SchemaProvider
{
    public static async IAsyncEnumerable<string> InitializeAsync(IKernel kernel)
    {
        await foreach (var schema in SchemasDefinitions.GetSchemasAsync())
        {
            var schemaText = await schema.FormatAsync(YamlSchemaFormatter.Instance).ConfigureAwait(false);

            await kernel.Memory.SaveInformationAsync("schemas", schemaText, schema.Name).ConfigureAwait(false);

            yield return schema.Name;
        }
    }
}
