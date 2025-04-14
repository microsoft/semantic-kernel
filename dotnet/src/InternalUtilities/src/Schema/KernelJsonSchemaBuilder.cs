// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary.
using System;
#pragma warning restore IDE0005 // Using directive is unnecessary.
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Microsoft.Extensions.AI;

#pragma warning disable IDE0010 // Add missing cases

namespace Microsoft.SemanticKernel;

// TODO: The JSON schema should match the JsonSerializerOptions used for actually performing
// the serialization, e.g. whether public fields should be included in the schema should
// match whether public fields will be serialized/deserialized. For now we can assume the
// default, but if/when a JSO is able to be provided via a Kernel, we should:
// 1) Use the JSO from the Kernel used to create the KernelFunction when constructing the schema
// 2) Check when the schema is being used (e.g. function calling) whether the JSO being used is equivalent to
//    whichever was used to build the schema, and if it's not, generate a new schema for that JSO
[ExcludeFromCodeCoverage]
internal static class KernelJsonSchemaBuilder
{
    private static JsonSerializerOptions? s_options;
    internal static readonly AIJsonSchemaCreateOptions s_schemaOptions = new()
    {
        IncludeSchemaKeyword = false,
        IncludeTypeInEnumSchemas = true,
        RequireAllProperties = false,
        DisallowAdditionalProperties = false,
    };

    private static readonly JsonElement s_trueSchemaAsObject = JsonDocument.Parse("{}").RootElement;
    private static readonly JsonElement s_falseSchemaAsObject = JsonDocument.Parse("""{"not":true}""").RootElement;

    [RequiresUnreferencedCode("Uses reflection to generate JSON schema, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to generate JSON schema, making it incompatible with AOT scenarios.")]
    public static KernelJsonSchema Build(Type type, string? description = null, AIJsonSchemaCreateOptions? configuration = null)
    {
        return Build(type, GetDefaultOptions(), description, configuration);
    }

    public static KernelJsonSchema Build(
        Type type,
        JsonSerializerOptions options,
        string? description = null,
        AIJsonSchemaCreateOptions? configuration = null)
    {
        configuration ??= s_schemaOptions;
        // To be compatible with the previous behavior of MEAI 9.3.0 (when description is empty, should not be included in the schema)
        string? schemaDescription = string.IsNullOrEmpty(description) ? null : description;
        JsonElement schemaDocument = AIJsonUtilities.CreateJsonSchema(type, schemaDescription, serializerOptions: options, inferenceOptions: configuration);
        switch (schemaDocument.ValueKind)
        {
            case JsonValueKind.False:
                schemaDocument = s_falseSchemaAsObject;
                break;
            case JsonValueKind.True:
                schemaDocument = s_trueSchemaAsObject;
                break;
        }

        return KernelJsonSchema.Parse(schemaDocument.GetRawText());
    }

    [RequiresUnreferencedCode("Uses JsonStringEnumConverter and DefaultJsonTypeInfoResolver classes, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses JsonStringEnumConverter and DefaultJsonTypeInfoResolver classes, making it incompatible with AOT scenarios.")]
    private static JsonSerializerOptions GetDefaultOptions()
    {
        if (s_options is null)
        {
            JsonSerializerOptions options = new()
            {
                TypeInfoResolver = new DefaultJsonTypeInfoResolver(),
                Converters = { new JsonStringEnumConverter() },
            };
            options.MakeReadOnly();
            s_options = options;
        }

        return s_options;
    }
}
