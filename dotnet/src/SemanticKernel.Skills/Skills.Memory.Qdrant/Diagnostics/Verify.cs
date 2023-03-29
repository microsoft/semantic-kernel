// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.Diagnostics;

internal static class Verify
{
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static void True(bool value, string message)
    {
        if (!value)
        {
            throw new ArgumentException(message);
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static void False(bool value, string message)
    {
        if (value)
        {
            throw new ArgumentException(message);
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNull([NotNull] object? obj, string message)
    {
        if (obj != null) { return; }

        throw new ArgumentNullException(null, message);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void ArgNotNull([NotNull] object? obj, string paramName, [CallerMemberName] string? caller = default)
    {
        if (obj != null) { return; }

        throw new ArgumentNullException(paramName, $"Parameter {paramName} cannot be null." + (!string.IsNullOrEmpty(caller) ? $"({caller})" : string.Empty));
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNullOrEmpty([NotNull] string? str, string message)
    {
        NotNull(str, message);
        if (!string.IsNullOrWhiteSpace(str)) { return; }

        throw new ArgumentOutOfRangeException(message);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void ArgNotNullOrEmpty([NotNull] string? str, string paramName, [CallerMemberName] string? caller = default)
    {
        NotNull(str, paramName);
        if (!string.IsNullOrWhiteSpace(str)) { return; }

        throw new ArgumentException(paramName, $"Parameter {paramName} cannot be empty." + (!string.IsNullOrEmpty(caller) ? $"({caller})" : string.Empty));
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void ArgNotNullOrEmpty<TData>([NotNull] IEnumerable<TData>? array, string paramName, [CallerMemberName] string? caller = default)
    {
        NotNull(array, paramName);
        if (array.Any()) { return; }

        throw new ArgumentException(paramName, $"Parameter {paramName} cannot be empty." + (!string.IsNullOrEmpty(caller) ? $"({caller})" : string.Empty));
    }

    internal static void StartsWith(string text, string prefix, string message)
    {
        NotNullOrEmpty(text, "The text to verify cannot be empty");
        NotNullOrEmpty(prefix, "The prefix to verify is empty");
        if (text.StartsWith(prefix, StringComparison.InvariantCultureIgnoreCase)) { return; }

        throw new ArgumentException(message);
    }

    internal static void DirectoryExists(string path)
    {
        if (Directory.Exists(path)) { return; }

        throw new ArgumentException($"Directory not found: {path}");
    }

    internal static void NotNullOrEmpty<T>(IList<T> list, string message)
    {
        if (list == null || list.Count == 0)
        {
            throw new ArgumentOutOfRangeException(message);
        }
    }

    public static void Equals<T>(T value, T test, string message)
        where T : IComparable<T>
    {
        int cmp = value.CompareTo(test);
        if (cmp != 0)
        {
            throw new ArgumentException(message);
        }
    }

    // internal static void Contains<T>(IDictionary<string, T> dictionary, string key, string message)
    // {
    //     if (dictionary.ContainsKey(key)) return;
    //     throw new Exception(message);
    // }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void LessThan<T>(T value, T max, string message)
        where T : IComparable<T>
    {
        if (value.CompareTo(max) >= 0) { throw new ArgumentOutOfRangeException(message); }
    }

    // internal static void LessThanEquals<T>(T value, T max, string message)
    //     where T : IComparable<T>
    // {
    //     if (value.CompareTo(max) > 0) throw new ArgumentOutOfRangeException(message);
    // }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void GreaterThan<T>(T value, T min, string message)
        where T : IComparable<T>
    {
        if (value.CompareTo(min) <= 0) { throw new ArgumentOutOfRangeException(message); }
    }

    // internal static void GreaterThanEquals<T>(T value, T min, string message)
    //     where T : IComparable<T>
    // {
    //     if (value.CompareTo(min) < 0) throw new ArgumentOutOfRangeException(message);
    // }
    //
    // internal static void InRange<T>(T value, T min, T max, string arg)
    //     where T : IComparable<T>
    // {
    //     if (value.CompareTo(min) < 0 || value.CompareTo(max) > 0)
    //     {
    //         throw new ArgumentOutOfRangeException(arg);
    //     }
    // }

    public static void IsValidUrl(string name, string url, bool requireHttps, bool allowReservedIp, bool allowQuery)
    {
        static bool IsReservedIpAddress(string host)
        {
            return host.StartsWith("0.", true, CultureInfo.InvariantCulture) ||
                   host.StartsWith("10.", true, CultureInfo.InvariantCulture) ||
                   host.StartsWith("127.", true, CultureInfo.InvariantCulture) ||
                   host.StartsWith("169.254.", true, CultureInfo.InvariantCulture) ||
                   host.StartsWith("192.0.0.", true, CultureInfo.InvariantCulture) ||
                   host.StartsWith("192.88.99.", true, CultureInfo.InvariantCulture) ||
                   host.StartsWith("192.168.", true, CultureInfo.InvariantCulture) ||
                   host.StartsWith("255.255.255.255", true, CultureInfo.InvariantCulture);
        }

        if (string.IsNullOrEmpty(url))
        {
            throw new ArgumentException($"The {name} is empty", name);
        }

        if (requireHttps && url.ToUpperInvariant().StartsWith("HTTP://", true, CultureInfo.InvariantCulture))
        {
            throw new ArgumentException($"The {name} `{url}` is not safe, it must start with https://", name);
        }

        if (requireHttps && !url.ToUpperInvariant().StartsWith("HTTPS://", true, CultureInfo.InvariantCulture))
        {
            throw new ArgumentException($"The {name} `{url}` is incomplete, enter a valid URL starting with 'https://", name);
        }

        bool result = Uri.TryCreate(url, UriKind.Absolute, out var uri);
        if (!result || string.IsNullOrEmpty(uri.Host))
        {
            throw new ArgumentException($"The {name} `{url}` is not valid", name);
        }

        if (requireHttps && uri.Scheme != Uri.UriSchemeHttps)
        {
            throw new ArgumentException($"The {name} `{url}` is not safe, it must start with https://", name);
        }

        if (!allowReservedIp && (uri.IsLoopback || IsReservedIpAddress(uri.Host)))
        {
            throw new ArgumentException($"The {name} `{url}` is not safe, it cannot point to a reserved network address", name);
        }

        if (!allowQuery && !string.IsNullOrEmpty(uri.Query))
        {
            throw new ArgumentException($"The {name} `{url}` is not valid, it cannot contain query parameters", name);
        }

        if (!string.IsNullOrEmpty(uri.Fragment))
        {
            throw new ArgumentException($"The {name} `{url}` is not valid, it cannot contain URL fragments", name);
        }
    }
}
