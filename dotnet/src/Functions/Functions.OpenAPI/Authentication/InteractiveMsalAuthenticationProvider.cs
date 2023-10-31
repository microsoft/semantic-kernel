// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Identity.Client;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;

/// <summary>
/// Uses the Microsoft Authentication Library (MSAL) to authenticate HTTP requests.
/// </summary>
public class InteractiveMsalAuthenticationProvider : BearerAuthenticationProvider
{
    /// <summary>
    /// Creates an instance of the <see cref="InteractiveMsalAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="clientId">Client ID of the caller.</param>
    /// <param name="tenantId">Tenant ID of the target resource.</param>
    /// <param name="scopes">Requested scopes.</param>
    /// <param name="redirectUri">Redirect URI.</param>
    public InteractiveMsalAuthenticationProvider(string clientId, string tenantId, string[] scopes, Uri redirectUri)
        : base(() => GetTokenAsync(clientId, tenantId, scopes, redirectUri))
    {
    }

    /// <summary>
    /// Gets an access token using the Microsoft Authentication Library (MSAL).
    /// </summary>
    /// <param name="clientId">Client ID of the caller.</param>
    /// <param name="tenantId">Tenant ID of the target resource.</param>
    /// <param name="scopes">Requested scopes.</param>
    /// <param name="redirectUri">Redirect URI.</param>
    /// <returns>Access token.</returns>
    private static async Task<string> GetTokenAsync(string clientId, string tenantId, string[] scopes, Uri redirectUri)
    {
        IPublicClientApplication app = PublicClientApplicationBuilder.Create(clientId)
            .WithRedirectUri(redirectUri.ToString())
            .WithTenantId(tenantId)
            .Build();

        IEnumerable<IAccount> accounts = await app.GetAccountsAsync().ConfigureAwait(false);
        AuthenticationResult result;
        try
        {
            result = await app.AcquireTokenSilent(scopes, accounts.FirstOrDefault())
                .ExecuteAsync().ConfigureAwait(false);
        }
        catch (MsalUiRequiredException)
        {
            // A MsalUiRequiredException happened on AcquireTokenSilent.
            // This indicates you need to call AcquireTokenInteractive to acquire a token
            result = await app.AcquireTokenInteractive(scopes)
                .ExecuteAsync().ConfigureAwait(false);
        }

        return result.AccessToken;
    }
}
