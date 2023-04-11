// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using static System.Net.Mime.MediaTypeNames;

namespace Microsoft.SemanticKernel.Text;

internal static class StringExtensions
{
    [SuppressMessage("Globalization", "CA1309:Use ordinal StringComparison", Justification = "By design")]
    internal static bool EqualsIgnoreCase(this string src, string value)
    {
        return src.Equals(value, StringComparison.InvariantCultureIgnoreCase);
    }

    internal static string NormalizeLineEndings(this string src)
    {
        return src.Replace("\r\n", "\n");
    }

    internal static string[] SplitEx(this string src, char separator, StringSplitOptions options)
    {
        return src.Split(new[] { separator }, StringSplitOptions.RemoveEmptyEntries);
    }

    public static bool IsNullOrEmpty([NotNullWhen(false)] this string? data)
    {
        return string.IsNullOrEmpty(data);
    }

    public static bool IsNullOrWhitespace([NotNullWhen(false)] this string? data)
    {
        return string.IsNullOrWhiteSpace(data);
    }

    internal static bool ContainsEx(this string src, string value, StringComparison comparison)
    {
        return src.IndexOf(value, StringComparison.InvariantCultureIgnoreCase) >= 0;
    }
}
