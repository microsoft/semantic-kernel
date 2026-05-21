// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;

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
    public static async Task ValidateAsync(
        Uri url,
        RestApiOperationServerUrlValidationOptions? options,
        CancellationToken cancellationToken = default)
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
            return;
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
                $"To allow this URL, add it to " +
                $"{nameof(RestApiOperationServerUrlValidationOptions)}.{nameof(RestApiOperationServerUrlValidationOptions.AllowedBaseUrls)}.");
        }

        // 3. Implicit private-IP gate.
        if (options.AllowPrivateNetworkAccess)
        {
            return;
        }

        await EnsurePublicHostAsync(url, cancellationToken).ConfigureAwait(false);
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

    private static async Task EnsurePublicHostAsync(Uri url, CancellationToken cancellationToken)
    {
        var host = url.DnsSafeHost;

        // Case 1: literal IP in the URL.
        if (url.HostNameType == UriHostNameType.IPv4 || url.HostNameType == UriHostNameType.IPv6)
        {
            if (!IPAddress.TryParse(host, out var ip))
            {
                // Should be unreachable — .NET's Uri already classified this as an IP address.
                // Fail closed: block the request rather than silently skipping validation.
                throw new InvalidOperationException(
                    $"The server URL '{url}' has a host identified as an IP address but could not be parsed. The request is blocked as a precaution.");
            }

            EnsurePublicAddress(url, ip);
            return;
        }

        // Case 2: hostname - resolve and validate every returned address (defeats DNS rebinding).
        IPAddress[] addresses;
        try
        {
#if NET
            addresses = await Dns.GetHostAddressesAsync(host, cancellationToken).ConfigureAwait(false);
#else
            addresses = await Dns.GetHostAddressesAsync(host).ConfigureAwait(false);
            cancellationToken.ThrowIfCancellationRequested();
#endif
        }
        catch (SocketException)
        {
            // DNS resolution failed. Fall through and let the HTTP layer surface the error.
            // This does not create an SSRF risk: an unresolvable host cannot reach a private
            // address either. Throwing here would also break legitimate scenarios where the
            // host is temporarily unreachable from the validating machine but resolvable later.
            return;
        }

        if (addresses is null || addresses.Length == 0)
        {
            return;
        }

        foreach (var address in addresses)
        {
            EnsurePublicAddress(url, address);
        }
    }

    private static void EnsurePublicAddress(Uri url, IPAddress address)
    {
        if (TryClassifyNonPublic(address, out var category))
        {
            throw new InvalidOperationException(
                $"The request URI '{url}' is not allowed: host resolves to a {category} address ({address}), " +
                $"which is blocked by default to prevent Server-Side Request Forgery (SSRF). " +
                $"To allow this URL, add it to " +
                $"{nameof(RestApiOperationServerUrlValidationOptions)}.{nameof(RestApiOperationServerUrlValidationOptions.AllowedBaseUrls)} " +
                $"or set {nameof(RestApiOperationServerUrlValidationOptions)}.{nameof(RestApiOperationServerUrlValidationOptions.AllowPrivateNetworkAccess)} = true.");
        }
    }

    /// <summary>
    /// Returns true and sets <paramref name="category"/> to a human-readable label when the
    /// supplied address is in a non-public IP range that should be blocked by default.
    /// </summary>
    internal static bool TryClassifyNonPublic(IPAddress address, out string category)
    {
        // Normalize IPv4-mapped IPv6 (::ffff:a.b.c.d) to its IPv4 form so the v4 checks apply.
        if (address.AddressFamily == AddressFamily.InterNetworkV6 && IsIPv4MappedToIPv6(address))
        {
            address = MapToIPv4(address);
        }

        if (address.AddressFamily == AddressFamily.InterNetwork)
        {
            return TryClassifyIPv4(address, out category);
        }

        if (address.AddressFamily == AddressFamily.InterNetworkV6)
        {
            return TryClassifyIPv6(address, out category);
        }

        // Not IPv4 or IPv6 - reject conservatively.
        category = "non-IP";
        return true;
    }

    private static bool TryClassifyIPv4(IPAddress address, out string category)
    {
        var bytes = address.GetAddressBytes();
        var b0 = bytes[0];
        var b1 = bytes[1];
        var b2 = bytes[2];

        // 0.0.0.0/8 - "this network", unspecified.
        if (b0 == 0)
        {
            category = "unspecified";
            return true;
        }

        // 10.0.0.0/8
        if (b0 == 10)
        {
            category = "private (RFC1918)";
            return true;
        }

        // 127.0.0.0/8 - loopback.
        if (b0 == 127)
        {
            category = "loopback";
            return true;
        }

        // 169.254.0.0/16 - link-local (includes cloud metadata 169.254.169.254).
        if (b0 == 169 && b1 == 254)
        {
            category = "link-local";
            return true;
        }

        // 172.16.0.0/12
        if (b0 == 172 && b1 >= 16 && b1 <= 31)
        {
            category = "private (RFC1918)";
            return true;
        }

        // 192.168.0.0/16
        if (b0 == 192 && b1 == 168)
        {
            category = "private (RFC1918)";
            return true;
        }

        // 100.64.0.0/10 - carrier-grade NAT.
        if (b0 == 100 && b1 >= 64 && b1 <= 127)
        {
            category = "carrier-grade NAT";
            return true;
        }

        // 198.18.0.0/15 - benchmarking.
        if (b0 == 198 && (b1 == 18 || b1 == 19))
        {
            category = "benchmarking";
            return true;
        }

        // 192.0.0.0/24 (IETF protocol assignments) and 192.0.2.0/24 (TEST-NET-1).
        if (b0 == 192 && b1 == 0 && (b2 == 0 || b2 == 2))
        {
            category = "reserved";
            return true;
        }

        // 198.51.100.0/24 (TEST-NET-2).
        if (b0 == 198 && b1 == 51 && b2 == 100)
        {
            category = "reserved";
            return true;
        }

        // 203.0.113.0/24 (TEST-NET-3).
        if (b0 == 203 && b1 == 0 && b2 == 113)
        {
            category = "reserved";
            return true;
        }

        // 224.0.0.0/4 - multicast.
        if (b0 >= 224 && b0 <= 239)
        {
            category = "multicast";
            return true;
        }

        // 240.0.0.0/4 - reserved (includes 255.255.255.255 broadcast).
        if (b0 >= 240)
        {
            category = "reserved";
            return true;
        }

        category = string.Empty;
        return false;
    }

    private static bool TryClassifyIPv6(IPAddress address, out string category)
    {
        if (IPAddress.IsLoopback(address))
        {
            category = "loopback";
            return true;
        }

        var bytes = address.GetAddressBytes();

        // :: (unspecified)
        if (address.Equals(IPAddress.IPv6None))
        {
            category = "unspecified";
            return true;
        }

        // fe80::/10 - link-local.
        if (bytes[0] == 0xfe && (bytes[1] & 0xC0) == 0x80)
        {
            category = "link-local";
            return true;
        }

        // fc00::/7 - unique local (private).
        if ((bytes[0] & 0xfe) == 0xfc)
        {
            category = "private (IPv6 ULA)";
            return true;
        }

        // ff00::/8 - multicast.
        if (bytes[0] == 0xff)
        {
            category = "multicast";
            return true;
        }

        // 2001:db8::/32 - documentation.
        if (bytes[0] == 0x20 && bytes[1] == 0x01 && bytes[2] == 0x0d && bytes[3] == 0xb8)
        {
            category = "reserved";
            return true;
        }

        category = string.Empty;
        return false;
    }

    private static bool IsIPv4MappedToIPv6(IPAddress address)
    {
#if NET
        return address.IsIPv4MappedToIPv6;
#else
        var bytes = address.GetAddressBytes();
        if (bytes.Length != 16)
        {
            return false;
        }
        for (int i = 0; i < 10; i++)
        {
            if (bytes[i] != 0)
            {
                return false;
            }
        }
        return bytes[10] == 0xff && bytes[11] == 0xff;
#endif
    }

    private static IPAddress MapToIPv4(IPAddress address)
    {
#if NET
        return address.MapToIPv4();
#else
        var bytes = address.GetAddressBytes();
        var v4 = new byte[4] { bytes[12], bytes[13], bytes[14], bytes[15] };
        return new IPAddress(v4);
#endif
    }
}
