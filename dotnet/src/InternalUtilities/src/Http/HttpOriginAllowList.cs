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
    /// Creates a validated, read-only copy of the allowed HTTP origins.
    /// </summary>
    /// <param name="origins">The origins to allow, or <see langword="null"/> when no origin policy is configured.</param>
    /// <param name="paramName">The name of the setting being configured, reported in validation errors.</param>
    /// <returns>The validated origins, or <see langword="null"/> when no origin policy is configured.</returns>
    /// <exception cref="ArgumentException">
    /// An entry is null or is not an absolute HTTP or HTTPS URI containing only a scheme, valid host, and optional port.
    /// </exception>
    public static IReadOnlyList<Uri>? Create(IEnumerable<Uri>? origins, string paramName)
    {
        if (origins is null)
        {
            return null;
        }

        var allowedOrigins = new List<Uri>();
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

        return allowedOrigins.AsReadOnly();
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
    public static bool Contains(IReadOnlyList<Uri>? allowedOrigins, Uri uri)
    {
        if (allowedOrigins is not { Count: > 0 } || !uri.IsAbsoluteUri || GetAsciiHost(uri) is not { } host)
        {
            return false;
        }

        foreach (var origin in allowedOrigins)
        {
            if (string.Equals(uri.Scheme, origin.Scheme, StringComparison.OrdinalIgnoreCase) &&
                string.Equals(host, origin.IdnHost, StringComparison.OrdinalIgnoreCase) &&
                uri.Port == origin.Port)
            {
                return true;
            }
        }

        return false;
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
}
