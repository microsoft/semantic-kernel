// Copyright (c) Microsoft. All rights reserved.

internal sealed class AppConfig
{
    /// <summary>
    /// The configuration for the Azure EntraId authentication.
    /// </summary>
    public AzureEntraIdConfig? AzureEntraId { get; set; }

    /// <summary>
    /// Ensures that the configuration is valid.
    /// </summary>
    internal void Validate()
    {
        ArgumentNullException.ThrowIfNull(this.AzureEntraId?.ClientId, nameof(this.AzureEntraId.ClientId));
        ArgumentNullException.ThrowIfNull(this.AzureEntraId?.TenantId, nameof(this.AzureEntraId.TenantId));

        if (this.AzureEntraId.InteractiveBrowserAuthentication)
        {
            ArgumentNullException.ThrowIfNull(this.AzureEntraId.InteractiveBrowserRedirectUri, nameof(this.AzureEntraId.InteractiveBrowserRedirectUri));
        }
        else
        {
            ArgumentNullException.ThrowIfNull(this.AzureEntraId?.ClientSecret, nameof(this.AzureEntraId.ClientSecret));
        }
    }

    internal sealed class AzureEntraIdConfig
    {
        /// <summary>
        /// App Registration Client Id
        /// </summary>
        public string? ClientId { get; set; }

        /// <summary>
        /// App Registration Tenant Id
        /// </summary>
        public string? TenantId { get; set; }

        /// <summary>
        /// The client secret to use for the Azure EntraId authentication.
        /// </summary>
        /// <remarks>
        /// This is required if InteractiveBrowserAuthentication is false. (App Authentication)
        /// </remarks>
        public string? ClientSecret { get; set; }

        /// <summary>
        /// Specifies whether to use interactive browser authentication (Delegated User Authentication) or App authentication.
        /// </summary>
        public bool InteractiveBrowserAuthentication { get; set; }

        /// <summary>
        /// When using interactive browser authentication, the redirect URI to use.
        /// </summary>
        public string? InteractiveBrowserRedirectUri { get; set; } = "http://localhost";
    }
}
