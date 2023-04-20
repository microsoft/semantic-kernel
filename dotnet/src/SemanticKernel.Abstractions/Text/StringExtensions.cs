// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Text;

internal static class StringExtensions
{
    internal static string NormalizeLineEndings(this string src)
    {
        return src.Replace("\r\n", "\n");
    }

    internal static string[] SplitEx(this string src, char separator, StringSplitOptions options = StringSplitOptions.None)
    {
        return src.Split(new[] { separator }, options);
    }

    internal static string[] SplitEx(this string src, string separator, StringSplitOptions options = StringSplitOptions.None)
    {
        return src.Split(new[] { separator }, options);
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
