// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Diagnostics;

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
    internal static void NotNull([NotNull] object? obj, string message)
    {
        if (obj != null) { return; }

        throw new ArgumentNullException(null, message);
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

    internal static void NotNullOrEmpty<T>(IList<T> list, string message)
    {
        if (list == null || list.Count == 0)
        {
            throw new ArgumentOutOfRangeException(message);
        }
    }

    public static void IsValidUrl(string name, string url, bool requireHttps, bool allowReservedIp, bool allowQuery)
    {
        static bool IsReservedIpAddress(string host)
        {
            return host.StartsWith("0.", StringComparison.Ordinal) ||
                   host.StartsWith("10.", StringComparison.Ordinal) ||
                   host.StartsWith("127.", StringComparison.Ordinal) ||
                   host.StartsWith("169.254.", StringComparison.Ordinal) ||
                   host.StartsWith("192.0.0.", StringComparison.Ordinal) ||
                   host.StartsWith("192.88.99.", StringComparison.Ordinal) ||
                   host.StartsWith("192.168.", StringComparison.Ordinal) ||
                   host.StartsWith("255.255.255.255", StringComparison.Ordinal);
        }

        if (string.IsNullOrEmpty(url))
        {
            throw new ArgumentException($"The {name} is empty", name);
        }

        if (requireHttps && url.StartsWith("http://", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException($"The {name} `{url}` is not safe, it must start with https://", name);
        }

        if (requireHttps && !url.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
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
