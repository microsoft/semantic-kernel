﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using JsonSchemaMapper;

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
    private static readonly JsonSerializerOptions s_options = CreateDefaultOptions();
    private static readonly JsonSchemaMapperConfiguration s_config = new()
    {
        IncludeSchemaVersion = false,
        IncludeTypeInEnums = true,
        TreatNullObliviousAsNonNullable = true,
    };

    public static KernelJsonSchema Build(JsonSerializerOptions? options, Type type, string? description = null)
    {
        options ??= s_options;

        JsonNode jsonSchema = options.GetJsonSchema(type, s_config);
        Debug.Assert(jsonSchema.GetValueKind() is JsonValueKind.Object or JsonValueKind.False or JsonValueKind.True);

        if (jsonSchema is not JsonObject jsonObj)
        {
            // Transform boolean schemas into object equivalents.
            jsonObj = jsonSchema.GetValue<bool>()
                ? new JsonObject()
                : new JsonObject { ["not"] = true };
        }

        if (!string.IsNullOrWhiteSpace(description))
        {
            jsonObj["description"] = description;
        }

        return KernelJsonSchema.Parse(jsonObj.ToJsonString(options));
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
