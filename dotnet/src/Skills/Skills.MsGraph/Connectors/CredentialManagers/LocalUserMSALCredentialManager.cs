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
public sealed class LocalUserMSALCredentialManager
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
    private LocalUserMSALCredentialManager(StorageCreationProperties storage, MsalCacheHelper cacheHelper)
    {
        this._publicClientApplications = new ConcurrentDictionary<string, IPublicClientApplication>(StringComparer.OrdinalIgnoreCase);
        this._storageProperties = storage;
        this._cacheHelper = cacheHelper;
        this._cacheHelper.VerifyPersistence();
    }

    /// <summary>
    /// Creates a new instance of the <see cref="LocalUserMSALCredentialManager"/> class.
    /// </summary>
    /// <returns>A task that represents the asynchronous operation. The task result contains the created <see cref="LocalUserMSALCredentialManager"/>.</returns>
    public static async Task<LocalUserMSALCredentialManager> CreateAsync()
    {
        // Initialize persistent storage for the token cache
        const string CacheSchemaName = "com.microsoft.semantickernel.tokencache";

        var storage = new StorageCreationPropertiesBuilder("sk.msal.cache", MsalCacheHelper.UserRootDirectory)
            .WithMacKeyChain(
                serviceName: $"{CacheSchemaName}.service",
                accountName: $"{CacheSchemaName}.account")
            .WithLinuxKeyring(
                schemaName: CacheSchemaName,
                collection: MsalCacheHelper.LinuxKeyRingDefaultCollection,
                secretLabel: "MSAL token cache for Semantic Kernel skills.",
                attribute1: new KeyValuePair<string, string>("Version", "1"),
                attribute2: new KeyValuePair<string, string>("Product", "SemanticKernel"))
            .Build();

        var cacheHelper = await MsalCacheHelper.CreateAsync(storage).ConfigureAwait(false);

        return new LocalUserMSALCredentialManager(storage, cacheHelper);
    }

    /// <summary>
    /// Acquires an access token for the specified client ID, tenant ID, scopes, and redirect URI.
    /// </summary>
    /// <param name="clientId">The client ID of the application.</param>
    /// <param name="tenantId">The tenant ID of the application.</param>
    /// <param name="scopes">The scopes for which the access token is requested.</param>
    /// <param name="redirectUri">The redirect URI of the application.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the access token.</returns>
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
            // throws MsalException
        }

        return result.AccessToken;
    }

    /// <summary>
    /// Returns a key for the public client application dictionary.
    /// </summary>
    private string PublicClientApplicationsKey(string clientId, string tenantId) => $"{clientId}_{tenantId}";
}
