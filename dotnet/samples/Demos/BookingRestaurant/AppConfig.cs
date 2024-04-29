// Copyright (c) Microsoft. All rights reserved.

internal sealed class AppConfig
{
    /// <summary>
    /// The business id of the booking service.
    /// </summary>
    public string? BookingBusinessId { get; set; }

    /// <summary>
    /// The service id of the booking service defined for the provided booking business.
    /// </summary>
    public string? BookingServiceId { get; set; }

    /// <summary>
    /// The configuration for the OpenAI chat completion.
    /// </summary>
    /// <remarks>
    /// This is ignored if using Azure OpenAI configuration.
    /// </remarks>
    public OpenAIConfig? OpenAI { get; set; }

    /// <summary>
    /// The configuration for the Azure OpenAI chat completion.
    /// </summary>
    /// <remarks>
    /// This is not required when OpenAI configuration is provided.
    /// </remarks>
    public AzureOpenAIConfig? AzureOpenAI { get; set; }

    /// <summary>
    /// The configuration for the Azure EntraId authentication.
    /// </summary>
    public AzureEntraIdConfig? AzureEntraId { get; set; }

    internal bool IsAzureOpenAIConfigured => this.AzureOpenAI?.DeploymentName is not null;

    /// <summary>
    /// Ensures that the configuration is valid.
    /// </summary>
    internal void Validate()
    {
        ArgumentNullException.ThrowIfNull(this.BookingBusinessId, nameof(this.BookingBusinessId));
        ArgumentNullException.ThrowIfNull(this.BookingServiceId, nameof(this.BookingServiceId));

        if (this.IsAzureOpenAIConfigured)
        {
            ArgumentNullException.ThrowIfNull(this.AzureOpenAI?.Endpoint, nameof(this.AzureOpenAI.Endpoint));
            ArgumentNullException.ThrowIfNull(this.AzureOpenAI?.ApiKey, nameof(this.AzureOpenAI.ApiKey));
        }
        else
        {
            ArgumentNullException.ThrowIfNull(this.OpenAI?.ModelId, nameof(this.OpenAI.ModelId));
            ArgumentNullException.ThrowIfNull(this.OpenAI?.ApiKey, nameof(this.OpenAI.ApiKey));
        }
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

    internal sealed class OpenAIConfig
    {
        /// <summary>
        /// The model ID to use for the OpenAI chat completion.
        /// Available Chat Completion models can be found at https://platform.openai.com/docs/models.
        /// </summary>
        public string? ModelId { get; set; }

        /// <summary>
        /// ApiKey to use for the OpenAI chat completion.
        /// </summary>
        public string? ApiKey { get; set; }

        /// <summary>
        /// Optional organization ID to use for the OpenAI chat completion.
        /// </summary>
        public string? OrgId { get; set; }
    }

    internal sealed class AzureOpenAIConfig
    {
        /// <summary>
        /// Deployment name of the Azure OpenAI resource.
        /// </summary>
        public string? DeploymentName { get; set; }

        /// <summary>
        /// Endpoint of the Azure OpenAI resource.
        /// </summary>
        public string? Endpoint { get; set; }

        /// <summary>
        /// ApiKey to use for the Azure OpenAI chat completion.
        /// </summary>
        public string? ApiKey { get; set; }
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
