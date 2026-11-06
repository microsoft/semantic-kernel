// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Classifies URLs against a <see cref="RestApiOperationServerUrlValidationOptions"/> policy
/// to prevent Server-Side Request Forgery (SSRF) via untrusted OpenAPI server URLs.
/// </summary>
internal static class ServerUrlValidator
{
    private const string ImplicitAllowedScheme = "https";

    /// <summary>
    /// Validates the given URL against the supplied policy and throws
    /// <see cref="InvalidOperationException"/> if the URL is not permitted.
    /// </summary>
    /// <param name="url">The fully resolved request URL to validate.</param>
    /// <param name="options">The validation policy. If <see langword="null"/>, the secure
    /// default policy (https-only and private/loopback/link-local IPs blocked) is applied.</param>
    /// <param name="cancellationToken">Cancellation token for the asynchronous DNS resolution.</param>
    /// <param name="dnsResolver">Optional DNS resolver for testing. When <see langword="null"/>,
    /// <see cref="Dns.GetHostAddressesAsync(string)"/> is used.</param>
    /// <returns>The validated DNS addresses to bind to the connection, or an empty array when DNS validation is bypassed.</returns>
    public static async Task<IPAddress[]> ValidateAsync(
        Uri url,
        RestApiOperationServerUrlValidationOptions? options,
        CancellationToken cancellationToken = default,
        Func<string, CancellationToken, Task<IPAddress[]>>? dnsResolver = null)
    {
        if (url is null)
        {
            throw new ArgumentNullException(nameof(url));
        }

        // Treat null as a default-constructed instance so protection is on by default.
        options ??= new RestApiOperationServerUrlValidationOptions();

        // 1. Explicit allow: a matching AllowedBaseUrls entry bypasses the implicit gates.
        if (TryMatchAllowedBaseUrl(url, options.AllowedBaseUrls))
        {
            return [];
        }

        // If the caller set AllowedBaseUrls and the URL didn't match, reject before further
        // checks so the failure message points the developer at the right knob.
        if (options.AllowedBaseUrls is { Count: > 0 })
        {
            throw new InvalidOperationException(
                $"The request URI '{url}' is not allowed. It does not match any of the allowed base URLs.");
        }

        // 2. Implicit scheme gate: only https is allowed by default.
        if (!string.Equals(url.Scheme, ImplicitAllowedScheme, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                $"The request URI scheme '{url.Scheme}' is not allowed. " +
                $"Only '{ImplicitAllowedScheme}' is permitted by default. " +
                "To allow this URL, add it to " +
                $"{nameof(RestApiOperationServerUrlValidationOptions)}.{nameof(RestApiOperationServerUrlValidationOptions.AllowedBaseUrls)}.");
        }

        // 3. Implicit private-IP gate.
        if (options.AllowPrivateNetworkAccess)
        {
            return [];
        }

        return await PublicNetworkAddressValidator.ValidateAsync(
            url, cancellationToken, dnsResolver,
            "To allow this URL, add it to " +
            $"{nameof(RestApiOperationServerUrlValidationOptions)}.{nameof(RestApiOperationServerUrlValidationOptions.AllowedBaseUrls)} " +
            $"or set {nameof(RestApiOperationServerUrlValidationOptions)}.{nameof(RestApiOperationServerUrlValidationOptions.AllowPrivateNetworkAccess)} = true.").ConfigureAwait(false);
    }

    private static bool TryMatchAllowedBaseUrl(Uri url, IReadOnlyList<Uri>? allowedBaseUrls)
    {
        if (allowedBaseUrls is not { Count: > 0 })
        {
            return false;
        }

        var urlPath = url.GetLeftPart(UriPartial.Path);

        foreach (var baseUrl in allowedBaseUrls)
        {
            if (baseUrl is null)
            {
                continue;
            }

            // Scheme, host, and port must all match for the explicit allow to apply.
            if (!string.Equals(url.Scheme, baseUrl.Scheme, StringComparison.OrdinalIgnoreCase) ||
                !string.Equals(url.Host, baseUrl.Host, StringComparison.OrdinalIgnoreCase) ||
                url.Port != baseUrl.Port)
            {
                continue;
            }

            var baseUrlPath = baseUrl.GetLeftPart(UriPartial.Path);
            var baseUrlWithSlash = baseUrlPath.EndsWith("/", StringComparison.Ordinal)
                ? baseUrlPath
                : baseUrlPath + "/";

            if (string.Equals(urlPath, baseUrlPath, StringComparison.OrdinalIgnoreCase) ||
                urlPath.StartsWith(baseUrlWithSlash, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
    }
}
