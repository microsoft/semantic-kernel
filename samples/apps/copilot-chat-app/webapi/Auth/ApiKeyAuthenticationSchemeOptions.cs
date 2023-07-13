// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Authentication;

namespace SemanticKernel.Service.Auth;

/// <summary>
/// Options for API key authentication.
/// </summary>
public class ApiKeyAuthenticationSchemeOptions : AuthenticationSchemeOptions
{
    /// <summary>
    /// The API key against which to authenticate.
    /// </summary>
    public string? ApiKey { get; set; }
}
