// Copyright (c) Microsoft. All rights reserved.

public static class StringExtensions
{
    public static string DefaultIfEmpty(this string text, string? defaultText = null) =>
        string.IsNullOrWhiteSpace(text) ? defaultText ?? string.Empty : text;
}
