// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Nodes;
using HandlebarsDotNet;

namespace Microsoft.SemanticKernel.PromptTemplates.Handlebars.Helpers;

/// <summary>
/// Extension class to register additional helpers as Kernel System helpers.
/// </summary>
internal static class KernelHelpersUtils
{
    /// <summary>
    /// Registers a helper with the Handlebars instance, throwing an exception if a helper with the same name is already registered.
    /// </summary>
    /// <param name="handlebarsInstance">The <see cref="IHandlebars"/>-instance.</param>
    /// <param name="helperName">The name of the helper.</param>
    /// <param name="helper">The helper to register.</param>
    internal static void RegisterHelperSafe(IHandlebars handlebarsInstance, string helperName, HandlebarsReturnHelper helper)
    {
        if (handlebarsInstance.Configuration.Helpers.ContainsKey(helperName))
        {
            throw new InvalidOperationException($"A helper with the name '{helperName}' is already registered.");
        }

        handlebarsInstance.RegisterHelper(helperName, helper);
    }

    /// <summary>
    /// Determines whether the specified type is a numeric type.
    /// </summary>
    /// <param name="type">The type to check.</param>
    /// <returns>True if the type is a numeric type; otherwise, false.</returns>
    public static bool IsNumericType(Type? type)
    {
        return type == typeof(nuint)
            || type == typeof(nint)
            || (type is not null &&
                Type.GetTypeCode(type) is
                    TypeCode.SByte or
                    TypeCode.Int16 or
                    TypeCode.Int32 or
                    TypeCode.Int64 or
                    TypeCode.Byte or
                    TypeCode.UInt16 or
                    TypeCode.UInt32 or
                    TypeCode.UInt64 or
                    TypeCode.Double or
                    TypeCode.Single or
                    TypeCode.Decimal);
    }

    /// <summary>
    /// Tries to parse the input as any of the numeric types.
    /// </summary>
    /// <param name="input">The input string to parse.</param>
    /// <returns>True if the input can be parsed as any of the numeric types; otherwise, false.</returns>
    public static bool TryParseAnyNumber(string? input)
    {
        // Check if input can be parsed as any of these numeric types.
        // We only need to check the largest types, as if they fail, the smaller types will also fail.
        return long.TryParse(input, out _) ||
            ulong.TryParse(input, out _) ||
            double.TryParse(input, out _) ||
            decimal.TryParse(input, out _);
    }

    /// <summary>
    /// Tries to convert a <see cref="JsonNode"/> object to a specific type.
    /// </summary>
    public static object? DeserializeJsonNode(JsonNode? jsonContent)
    {
        return jsonContent?.GetValueKind() switch
        {
            JsonValueKind.Array => jsonContent.AsArray(),
            JsonValueKind.Object => jsonContent.AsObject(),
            JsonValueKind.String => jsonContent.GetValue<string>(),
            _ => jsonContent
        };
    }
}
