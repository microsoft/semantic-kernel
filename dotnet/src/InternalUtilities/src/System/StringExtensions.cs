// Copyright (c) Microsoft. All rights reserved.


#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace System;
#pragma warning restore IDE0130

internal static class StringExtensions
{
    internal static string ReplaceLineEndingsWithLineFeed(this string src)
    {
#if NET6_0_OR_GREATER
        return src.ReplaceLineEndings("\n");
#else
        return src.Replace("\r\n", "\n");
#endif
    }
}
