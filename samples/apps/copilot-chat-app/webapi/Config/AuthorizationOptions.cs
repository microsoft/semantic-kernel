// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Identity.Web;

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration options for authorizing to the service.
/// </summary>
public class AuthorizationOptions
{
    public const string PropertyName = "Authorization";

    public enum AuthorizationType
    {
        None,
        ApiKey,
        AzureAd
    }

    /// <summary>
    /// Type of authorization.
    /// </summary>
    public AuthorizationType Type { get; set; }

    /// <summary>
    /// When <see cref="Type"/> is <see cref="AuthorizationType.ApiKey"/>, this is the API key to use.
    /// </summary>
    public string? ApiKey { get; set; }

    /// <summary>
    /// When <see cref="Type"/> is <see cref="AuthorizationType.AzureAd"/>, these are the Azure AD options to use.
    /// </summary>
    public AzureAdOptions? AzureAd { get; set; }

    /// <summary>
    /// Configuration options for Azure Active Directory (AAD) authorization.
    /// </summary>
    public class AzureAdOptions
    {
        /// <summary>
        /// AAD instance url, i.e., https://login.microsoftonline.com/
        /// </summary>
        public string? Instance { get; set; }

        /// <summary>
        /// Active directory/tenant ID
        /// </summary>
        public string? TenantId { get; set; }

        /// <summary>
        /// Application registration ID
        /// </summary>
        public string? ClientId { get; set; }

        /// <summary>
        /// Required scopes.
        /// </summary>
        public string? Scopes { get; set; }
    }
}
