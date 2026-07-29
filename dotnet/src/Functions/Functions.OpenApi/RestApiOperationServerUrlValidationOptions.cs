// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Options for validating server URLs before making HTTP requests in the OpenAPI plugin.
/// These options control the secure-by-default protection against Server-Side Request Forgery
/// (SSRF) attacks that the OpenAPI plugin applies to URLs derived from the OpenAPI document
/// (the <c>servers[].url</c> field and any server-variable substitutions).
/// </summary>
/// <remarks>
/// <para>
/// When <see cref="OpenApiFunctionExecutionParameters.ServerUrlValidationOptions"/> is left
/// <see langword="null"/>, a default-constructed instance of this class is applied. The default
/// policy is:
/// </para>
/// <list type="bullet">
///   <item><description>Only the <c>https</c> scheme is permitted for URLs that are not on the
///         <see cref="AllowedBaseUrls"/> allowlist.</description></item>
///   <item><description>Requests whose host resolves to a loopback, link-local (including the
///         cloud metadata endpoint <c>169.254.169.254</c>), private (RFC1918), IPv6 unique local
///         (<c>fc00::/7</c>), carrier-grade NAT, multicast, or reserved IP range are rejected.</description></item>
/// </list>
/// <para>
/// A URL that matches an entry in <see cref="AllowedBaseUrls"/> is an explicit allow and
/// bypasses both the implicit https-only gate and the private-IP gate, so an allowlist can be
/// used to opt specific intranet hosts back in.
/// </para>
/// <para>
/// <b>Known limitation:</b> URL validation is performed before the HTTP request is sent. If the
/// <see cref="System.Net.Http.HttpClient"/> used to invoke the plugin has automatic redirect
/// following enabled (the default), an attacker that controls a public host may redirect the
/// request to a private address. Configure your <see cref="System.Net.Http.HttpClient"/> with
/// <c>AllowAutoRedirect = false</c> when consuming OpenAPI documents from untrusted sources.
/// </para>
/// </remarks>
[Experimental("SKEXP0040")]
public class RestApiOperationServerUrlValidationOptions
{
    /// <summary>
    /// Gets or sets the explicit allowlist of base URLs. A request whose final URL matches one
    /// of these entries (same scheme, host, port, and path prefix) is permitted regardless of
    /// the implicit scheme and private-IP gates.
    /// </summary>
    /// <remarks>
    /// For example, with <c>AllowedBaseUrls = [new Uri("https://api.example.com/v1")]</c>:
    /// <c>https://api.example.com/v1/users</c> is allowed, <c>https://api.example.com/v2/...</c>
    /// is rejected, and <c>https://evil.com/...</c> is rejected. Query strings and fragments in
    /// the entries are ignored for comparison. Adding an <c>http://</c> entry (for example,
    /// <c>http://localhost:5000</c> or <c>http://intranet.corp</c>) is the recommended way to
    /// opt-in specific plaintext or intranet endpoints without weakening the global defaults.
    /// </remarks>
    public IReadOnlyList<Uri>? AllowedBaseUrls { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether requests to private, loopback, link-local, and
    /// other non-public IP ranges are permitted for URLs that are not covered by
    /// <see cref="AllowedBaseUrls"/>. The default is <see langword="false"/> (secure).
    /// </summary>
    /// <remarks>
    /// Setting this to <see langword="true"/> disables the SSRF protections that block requests
    /// to cloud metadata services (e.g. <c>169.254.169.254</c>), <c>localhost</c>, RFC1918
    /// networks, and similar ranges. Only enable this in trusted environments (such as local
    /// development). Prefer adding specific hosts to <see cref="AllowedBaseUrls"/> instead.
    /// </remarks>
    public bool AllowPrivateNetworkAccess { get; set; }
}
