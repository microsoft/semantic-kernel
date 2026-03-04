// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Options for validating server URLs before making HTTP requests in the OpenAPI plugin.
/// When configured, these options help prevent Server-Side Request Forgery (SSRF) attacks
/// by restricting which URLs the plugin is allowed to call.
/// </summary>
public class RestApiOperationServerUrlValidationOptions
{
    /// <summary>
    /// Gets or sets the allowed base URLs.
    /// If set, only requests to URLs that start with one of these base URLs will be permitted.
    /// For example, if <c>AllowedBaseUrls</c> contains <c>https://api.example.com</c>,
    /// then requests to <c>https://api.example.com/v1/users</c> will be allowed,
    /// but requests to <c>https://evil.com/data</c> will be blocked.
    /// If null, no base URL restriction is applied (scheme validation still applies).
    /// </summary>
    public IReadOnlyList<Uri>? AllowedBaseUrls { get; set; }

    /// <summary>
    /// Gets or sets the allowed URI schemes.
    /// If null or empty, only <c>https</c> is permitted.
    /// </summary>
    public IReadOnlyList<string>? AllowedSchemes { get; set; }
}
