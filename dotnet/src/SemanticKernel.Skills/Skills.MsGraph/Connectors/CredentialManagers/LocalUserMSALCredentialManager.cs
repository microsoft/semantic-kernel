// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Identity.Client;
using Microsoft.Identity.Client.Extensions.Msal;
using Microsoft.SemanticKernel.Skills.MsGraph.Connectors.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.MsGraph.Connectors.CredentialManagers;

/// <summary>
/// Manages acquiring and caching MSAL credentials locally.
/// **NOT for use in services or with shared profile scenarios.**
/// </summary>
/// <remarks>
/// https://learn.microsoft.com/azure/active-directory/develop/msal-net-token-cache-serialization?tabs=desktop
/// </remarks>
public class LocalUserMSALCredentialManager
{
    /// <summary>
    /// An in-memory cache of IPublicClientApplications by clientId and tenantId.
    /// </summary>
    private readonly ConcurrentDictionary<string, IPublicClientApplication> _publicClientApplications;

    /// <summary>
    /// Storage properties used by the token cache.
    /// </summary>
    private readonly StorageCreationProperties _storageProperties;

    /// <summary>
    /// Helper to create and manager the token cache.
    /// </summary>
    private readonly MsalCacheHelper _cacheHelper;

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalUserMSALCredentialManager"/> class.
    /// </summary>
    public LocalUserMSALCredentialManager()
    {
        this._publicClientApplications = new ConcurrentDictionary<string, IPublicClientApplication>(StringComparer.OrdinalIgnoreCase);

        // Initialize persistent storage for the token cache
        const string cacheSchemaName = "com.microsoft.semantickernel.tokencache";

        this._storageProperties = new StorageCreationPropertiesBuilder("sk.msal.cache", MsalCacheHelper.UserRootDirectory)
            .WithMacKeyChain(
                serviceName: $"{cacheSchemaName}.service",
                accountName: $"{cacheSchemaName}.account")
            .WithLinuxKeyring(
                schemaName: cacheSchemaName,
                collection: MsalCacheHelper.LinuxKeyRingDefaultCollection,
                secretLabel: "MSAL token cache for Semantic Kernel skills.",
                attribute1: new KeyValuePair<string, string>("Version", "1"),
                attribute2: new KeyValuePair<string, string>("Product", "SemanticKernel"))
            .Build();

        // TODO: remove sync wait, may cause deadlock
#pragma warning disable VSTHRD002 // Synchronously waiting on tasks or awaiters may cause deadlocks. Use await or JoinableTaskFactory.Run instead.
        this._cacheHelper = MsalCacheHelper.CreateAsync(this._storageProperties)
            .GetAwaiter()
            .GetResult();
#pragma warning restore VSTHRD002

        this._cacheHelper.VerifyPersistence();
    }

    /// <summary>
    /// Acquires an access token for the specified client ID, tenant ID, scopes, and redirect URI.
    /// </summary>
    public async Task<string> GetTokenAsync(string clientId, string tenantId, string[] scopes, Uri redirectUri)
    {
        Ensure.NotNullOrWhitespace(clientId, nameof(clientId));
        Ensure.NotNullOrWhitespace(tenantId, nameof(tenantId));
        Ensure.NotNull(redirectUri, nameof(redirectUri));
        Ensure.NotNull(scopes, nameof(scopes));

        IPublicClientApplication app = this._publicClientApplications.GetOrAdd(
            key: this.PublicClientApplicationsKey(clientId, tenantId),
            valueFactory: _ =>
            {
                IPublicClientApplication newPublicApp = PublicClientApplicationBuilder.Create(clientId)
                    .WithRedirectUri(redirectUri.ToString())
                    .WithTenantId(tenantId)
                    .Build();
                this._cacheHelper.RegisterCache(newPublicApp.UserTokenCache);
                return newPublicApp;
            });

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
            // throws MsalException
        }

        return result.AccessToken;
    }

    /// <summary>
    /// Returns a key for the public client application dictionary.
    /// </summary>
    private string PublicClientApplicationsKey(string clientId, string tenantId) => $"{clientId}_{tenantId}";
}
