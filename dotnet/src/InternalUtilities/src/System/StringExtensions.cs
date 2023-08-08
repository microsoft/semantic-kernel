// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace System;
#pragma warning restore IDE0130

internal static class StringExtensions
{
    internal static string NormalizeLineEndings(this string src)
    {
#if NET6_0_OR_GREATER
        return src.ReplaceLineEndings("\n");
#else
        return src.Replace("\r\n", "\n");
#endif
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
