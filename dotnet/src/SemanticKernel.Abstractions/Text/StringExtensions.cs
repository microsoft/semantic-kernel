// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Text;

internal static class StringExtensions
{
    internal static string NormalizeLineEndings(this string src)
    {
        return src.Replace("\r\n", "\n");
    }

    public static bool IsNullOrEmpty([NotNullWhen(false)] this string? data)
    {
        return string.IsNullOrEmpty(data);
    }

    public static bool IsNullOrWhitespace([NotNullWhen(false)] this string? data)
    {
        return string.IsNullOrWhiteSpace(data);
    }
}
