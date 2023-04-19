// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Identity.Client;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

/// <summary>
/// Uses the Microsoft Authentication Library (MSAL) to authenticate HTTP requests.
/// </summary>
public class MsalAuthenticationProvider : BearerAuthenticationProvider
{

    /// <summary>
    /// Creates an instance of the <see cref="MsalAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="clientId">Client ID of the caller.</param>
    /// <param name="tenantId">Tenant ID of the target resource.</param>
    /// <param name="scopes">Requested scopes.</param>
    /// <param name="resourceUri">URI for the target resource.</param>
    /// <param name="redirectUri">Redirect URI.</param>
    public MsalAuthenticationProvider(string clientId, string tenantId, string[] scopes, Uri resourceUri, Uri redirectUri)
        : base(async () => { return await GetTokenAsync(clientId, tenantId, scopes, resourceUri, redirectUri); })
    {
    }

    /// <summary>
    /// Gets an access token using the Microsoft Authentication Library (MSAL).
    /// </summary>
    /// <param name="clientId">Client ID of the caller.</param>
    /// <param name="tenantId">Tenant ID of the target resource.</param>
    /// <param name="scopes">Requested scopes.</param>
    /// <param name="resourceUri">URI for the target resource.</param>
    /// <param name="redirectUri">Redirect URI.</param>
    /// <returns>Access token.</returns>
    private static async Task<string> GetTokenAsync(string clientId, string tenantId, string[] scopes, Uri resourceUri, Uri redirectUri)
    {
        // Prefix scopes with the resource URI
        var prefix = resourceUri.ToString().TrimEnd('/') + '/';
        for (int i = 0; i < scopes.Length; i++)
        {
            if (!scopes[i].StartsWith(prefix, StringComparison.InvariantCultureIgnoreCase))
            {
                scopes[i] = prefix + scopes[i];
            }
        }

        IPublicClientApplication app = PublicClientApplicationBuilder.Create(clientId)
            .WithRedirectUri(redirectUri.ToString())
            .WithTenantId(tenantId)
            .Build();

        IEnumerable<IAccount> accounts = await app.GetAccountsAsync();
        AuthenticationResult result;
        try
        {
            result = await app.AcquireTokenSilent(scopes, accounts.FirstOrDefault())
                .ExecuteAsync();
        }
        catch (MsalUiRequiredException)
        {
            // A MsalUiRequiredException happened on AcquireTokenSilent.
            // This indicates you need to call AcquireTokenInteractive to acquire a token
            result = await app.AcquireTokenInteractive(scopes)
                .ExecuteAsync();
        }

        return result.AccessToken;
    }
}
