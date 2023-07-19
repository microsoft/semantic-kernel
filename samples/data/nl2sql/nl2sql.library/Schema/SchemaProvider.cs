// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Library.Schema;

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

/// <summary>
/// Responsible for loading the defined schemas into semantic memory.
/// </summary>
public static class SchemaProvider
{
    public const string MemoryCollectionName = "data-schemas";

    public static async Task InitializeAsync(IKernel kernel, IEnumerable<string> schemaPaths)
    {
        foreach (var schemaPath in schemaPaths)
        {
            var schema = await SchemaSerializer.ReadAsync(schemaPath).ConfigureAwait(false);

            var schemaText = await schema.FormatAsync(YamlSchemaFormatter.Instance).ConfigureAwait(false);

            await kernel.Memory.SaveInformationAsync(MemoryCollectionName, schemaText, schema.Name).ConfigureAwait(false);
        }
    }
}
