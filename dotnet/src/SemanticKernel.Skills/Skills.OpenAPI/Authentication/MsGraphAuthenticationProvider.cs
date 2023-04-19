// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

/// <summary>
/// Uses the Microsoft Authentication Library (MSAL) to authenticate HTTP requests to the Microsoft Graph.
/// </summary>
public class MsGraphAuthenticationProvider : MsalAuthenticationProvider
{
    private const string MsGraphUri = "https://graph.microsoft.com/";

    /// <summary>
    /// Creates an instance of the <see cref="MsGraphAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="clientId">Client ID of the caller.</param>
    /// <param name="tenantId">Tenant ID of the target resource.</param>
    /// <param name="scopes">Requested scopes.</param>
    /// <param name="redirectUri">Redirect URI.</param>
    public MsGraphAuthenticationProvider(string clientId, string tenantId, string[] scopes, Uri redirectUri)
        : base(clientId, tenantId, scopes, new Uri(MsGraphUri), redirectUri)
    {
    }
}
