using System;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using JsonSchemaMapper;

namespace Microsoft.SemanticKernel;

internal static class KernelJsonSchemaBuilder
{
    private static readonly JsonSchemaMapperConfiguration s_config = new() { IncludeSchemaVersion = false };
    private static readonly JsonSerializerOptions s_options = CreateDefaultOptions();

    public static KernelJsonSchema Build(JsonSerializerOptions? options, Type type, string? description = null)
    {
        options ??= s_options;

        JsonObject o = options.GetJsonSchema(type, s_config);
        if (!string.IsNullOrWhiteSpace(description))
        {
            o["description"] = description;
        }

        return KernelJsonSchema.Parse(JsonSerializer.Serialize(o, options));
    }

    private static JsonSerializerOptions CreateDefaultOptions()
    {
        JsonSerializerOptions options = new()
        {
            TypeInfoResolver = new DefaultJsonTypeInfoResolver(),
            Converters = { new JsonStringEnumConverter() },
        };
        options.MakeReadOnly();
        return options;
    }
}
