// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Validates allowed HTTP origins and checks whether requests match them.
/// </summary>
internal static class HttpOriginAllowList
{
    /// <summary>
    /// Validates and collects the allowed HTTP origins, keeping one entry per origin.
    /// </summary>
    /// <param name="origins">The origins to allow, or <see langword="null"/> when no origin policy is configured.</param>
    /// <param name="paramName">The name of the setting being configured, reported in validation errors.</param>
    /// <returns>The validated origins, or <see langword="null"/> when no origin policy is configured.</returns>
    /// <exception cref="ArgumentException">
    /// An entry is null or is not an absolute HTTP or HTTPS URI containing only a scheme, valid host, and optional port.
    /// </exception>
    public static HashSet<Uri>? Create(IEnumerable<Uri>? origins, string paramName)
    {
        if (origins is null)
        {
            return null;
        }

        var allowedOrigins = new HashSet<Uri>(OriginComparer.Instance);
        foreach (var origin in origins)
        {
            if (origin is null ||
                !origin.IsAbsoluteUri ||
                (origin.Scheme != Uri.UriSchemeHttp && origin.Scheme != Uri.UriSchemeHttps) ||
                origin.UserInfo.Length > 0 ||
                origin.AbsolutePath != "/" ||
                origin.Query.Length > 0 ||
                origin.Fragment.Length > 0 ||
                GetAsciiHost(origin) is null)
            {
                throw new ArgumentException(
                    "Allowed origins must be absolute HTTP or HTTPS URIs containing only a scheme, host, and optional port.",
                    paramName);
            }

            allowedOrigins.Add(origin);
        }

        return allowedOrigins;
    }

    /// <summary>
    /// Checks whether a request URI matches an allowed scheme, host, and port.
    /// </summary>
    /// <param name="allowedOrigins">The validated origins permitted by the application.</param>
    /// <param name="uri">The request URI to check.</param>
    /// <returns><see langword="true"/> if an origin matches; otherwise, <see langword="false"/>.</returns>
    /// <remarks>
    /// Scheme and host comparisons ignore case. Internationalized host names match their ASCII (punycode) form.
    /// Omitted ports use their scheme's default. Request paths do not affect matching.
    /// </remarks>
    public static bool Contains(HashSet<Uri>? allowedOrigins, Uri uri)
    {
        if (allowedOrigins is not { Count: > 0 } || !uri.IsAbsoluteUri || GetAsciiHost(uri) is null)
        {
            return false;
        }

        return allowedOrigins.Contains(uri);
    }

    /// <summary>
    /// Gets the ASCII hostname, or returns <see langword="null"/> if the hostname cannot be converted.
    /// </summary>
    private static string? GetAsciiHost(Uri uri)
    {
        try
        {
            return uri.IdnHost;
        }
        catch (UriFormatException)
        {
            return null;
        }
    }

    /// <summary>
    /// Compares validated URIs by origin, ignoring paths, queries, and fragments.
    /// </summary>
    private sealed class OriginComparer : IEqualityComparer<Uri>
    {
        internal static OriginComparer Instance { get; } = new();

        public bool Equals(Uri? x, Uri? y)
        {
            if (ReferenceEquals(x, y))
            {
                return true;
            }

            return x is not null && y is not null &&
                x.Port == y.Port &&
                string.Equals(x.Scheme, y.Scheme, StringComparison.OrdinalIgnoreCase) &&
                string.Equals(x.IdnHost, y.IdnHost, StringComparison.OrdinalIgnoreCase);
        }

        public int GetHashCode(Uri obj)
        {
            var comparer = StringComparer.OrdinalIgnoreCase;
            return (comparer.GetHashCode(obj.Scheme), comparer.GetHashCode(obj.IdnHost), obj.Port).GetHashCode();
        }
    }
}
