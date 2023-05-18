// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace SemanticKernel.Service.Options;

/// <summary>
/// Configuration options for authorizing to the service.
/// </summary>
public class ChatAuthenticationOptions
{
    public const string PropertyName = "Authentication";

    public enum AuthenticationType
    {
        None,
        AzureAd
    }

    /// <summary>
    /// Type of authorization.
    /// </summary>
    public AuthenticationType Type { get; set; } = AuthenticationType.None;

    /// <summary>
    /// When <see cref="Type"/> is <see cref="AuthenticationType.AzureAd"/>, these are the Azure AD options to use.
    /// </summary>
    [RequiredOnPropertyValue(nameof(Type), AuthenticationType.AzureAd)]
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
