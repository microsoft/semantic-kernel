// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;

namespace Step04;

internal static class JsonSchemaGenerator
{
    private static readonly AIJsonSchemaCreateOptions s_config = new()
    {
        TransformOptions = new()
        {
            DisallowAdditionalProperties = true,
            RequireAllProperties = true,
            MoveDefaultKeywordToDescription = true,
        }
    };

    /// <summary>
    /// Wrapper for generating a JSON schema as string from a .NET type.
    /// </summary>
    public static string FromType<TSchemaType>()
    {
        return KernelJsonSchemaBuilder.Build(typeof(TSchemaType), "Intent Result", s_config).AsJson();
    }
}
