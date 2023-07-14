// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Services;

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using SemanticKernel.Data.Nl2Sql.Exceptions;
using SemanticKernel.Data.Nl2Sql.Schema;

internal sealed class SchemaProvider
{
    private readonly IReadOnlyDictionary<string, SchemaDefinition> schemaMap;
    private readonly IDictionary<string, string> schemaCache;

    public static Func<IServiceProvider, SchemaProvider> Create(IConfiguration configuration)
    {
        return CreateProvider;

        SchemaProvider CreateProvider(IServiceProvider provider)
        {
            var schemas = GetSchemasAsync().ToArrayAsync().ConfigureAwait(false).GetAwaiter().GetResult();

            return new SchemaProvider(schemas.ToDictionary(s => s.Name));
        }
    }

    private SchemaProvider(IReadOnlyDictionary<string, SchemaDefinition> schemaMap)
    {
        this.schemaMap = schemaMap;
        this.schemaCache = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    }

    public IEnumerable<(string, SchemaDefinition)> Schemas => this.schemaMap.OrderBy(s => s.Key).Select(s => (s.Key, s.Value));

    public async Task<string> GetSchemaAsync(string schemaName)
    {
        if (!this.schemaCache.TryGetValue(schemaName, out string? schemaText))
        {
            if (!this.schemaMap.TryGetValue(schemaName, out SchemaDefinition? schema))
            {
                throw new UnknownSchemaException($"Unknown schema: {schemaName}");
            }

            schemaText = await schema.FormatAsync(PromptSchemaFormatter.Instance).ConfigureAwait(false);
        }

        return schemaText;
    }

    private static async IAsyncEnumerable<SchemaDefinition> GetSchemasAsync()
    {
        yield return await SchemaSerializer.ReadAsync(Path.Combine(Program.ConfigRoot, "adventureworks.json")).ConfigureAwait(false);
    }
}
