// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Identity.Client;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

/// <summary>
/// 
/// </summary>
public class MSALAuthenticationProvider : TokenAuthenticationProvider
{
    /// <summary>
    /// 
    /// </summary>
    /// <param name="clientId"></param>
    /// <param name="tenantId"></param>
    /// <param name="scopes"></param>
    /// <param name="redirectUri"></param>
    public MSALAuthenticationProvider(string clientId, string tenantId, string[] scopes, Uri redirectUri)
        : base(async () => { return await GetTokenAsync(clientId, tenantId, scopes, redirectUri); })
    {
    }

    private static async Task<string> GetTokenAsync(string clientId, string tenantId, string[] scopes, Uri redirectUri)
    {
        // TODO: format scopes

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
