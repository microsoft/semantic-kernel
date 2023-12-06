// Copyright (c) Microsoft. All rights reserved.

using System;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.PromptTemplate.Handlebars.Helpers;
#pragma warning restore IDE0130

/// <summary>
/// Extension class to register additional helpers as Kernel System helpers.
/// </summary>
public static class KernelHelpersUtils
{
    /// <summary>
    /// Determines whether the specified type is a numeric type.
    /// </summary>
    /// <param name="type">The type to check.</param>
    /// <returns>True if the type is a numeric type; otherwise, false.</returns>
    public static bool IsNumericType(Type? type)
    {
        return type is not null &&
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
                    TypeCode.Decimal;
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
}
