// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Library.Schema;

using System.IO;
using System.Text.Json;
using System.Threading.Tasks;

internal static class SchemaSerializer
{
    public static async Task<SchemaDefinition> ReadAsync(string path)
    {
        using var stream = File.OpenRead(path);

        return await ReadAsync(stream).ConfigureAwait(false);
    }

    public static async Task<SchemaDefinition> ReadAsync(Stream stream)
    {
        return
            await JsonSerializer.DeserializeAsync<SchemaDefinition>(
                stream,
                new JsonSerializerOptions
                {
                    PropertyNameCaseInsensitive = true
                }).ConfigureAwait(false) ??
            throw new JsonException("Unable to read schema.");
    }

    public static string ToJson(this SchemaDefinition schema)
    {
        return JsonSerializer.Serialize(schema, new JsonSerializerOptions { WriteIndented = true });
    }
}
