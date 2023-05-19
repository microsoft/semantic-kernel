// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Options;

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
    [Required]
    public AuthorizationType Type { get; set; } = AuthorizationType.None;

    /// <summary>
    /// When <see cref="Type"/> is <see cref="AuthorizationType.ApiKey"/>, this is the API key to use.
    /// </summary>
    [RequiredOnPropertyValue(nameof(Type), AuthorizationType.ApiKey, notEmptyOrWhitespace: true)]
    public string ApiKey { get; set; } = string.Empty;

    /// <summary>
    /// When <see cref="Type"/> is <see cref="AuthorizationType.AzureAd"/>, these are the Azure AD options to use.
    /// </summary>
    [RequiredOnPropertyValue(nameof(Type), AuthorizationType.AzureAd)]
    public AzureAdOptions? AzureAd { get; set; }

    /// <summary>
    /// Configuration options for Azure Active Directory (AAD) authorization.
    /// </summary>
    public class AzureAdOptions
    {
        /// <summary>
        /// AAD instance url, i.e., https://login.microsoftonline.com/
        /// </summary>
        [Required, NotEmptyOrWhitespace]
        public string Instance { get; set; } = string.Empty;

        /// <summary>
        /// Tenant (directory) ID
        /// </summary>
        [Required, NotEmptyOrWhitespace]
        public string TenantId { get; set; } = string.Empty;

        /// <summary>
        /// Application (client) ID
        /// </summary>
        [Required, NotEmptyOrWhitespace]
        public string ClientId { get; set; } = string.Empty;

        /// <summary>
        /// Required scopes.
        /// </summary>
        [Required]
        public string? Scopes { get; set; } = string.Empty;
    }
}
