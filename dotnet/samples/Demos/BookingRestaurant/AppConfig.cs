// Copyright (c) Microsoft. All rights reserved.


internal class AppConfig
{
    public string? BookingBusinessId { get; set; }

    public string? BookingServiceId { get; set; }

    public OpenAIConfig? OpenAI { get; set; }

    public AzureAdConfig? AzureAd { get; set; }

    public AzureOpenAIConfig? AzureOpenAI { get; set; }

    public bool IsAzureOpenAIConfigured => this.AzureOpenAI?.DeploymentName is not null;

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
        ArgumentNullException.ThrowIfNull(this.AzureAd?.ClientId, nameof(this.AzureAd.ClientId));
        ArgumentNullException.ThrowIfNull(this.AzureAd?.TenantId, nameof(this.AzureAd.TenantId));

        if (this.AzureAd.InteractiveBrowserAuthentication)
        {
            ArgumentNullException.ThrowIfNull(this.AzureAd.InteractiveBrowserRedirectUri, nameof(this.AzureAd.InteractiveBrowserRedirectUri));
        }
        else
        {
            ArgumentNullException.ThrowIfNull(this.AzureAd?.ClientSecret, nameof(this.AzureAd.ClientSecret));
        }
    }

    internal class OpenAIConfig
    {
        /// <summary>
        /// The model ID to use for the OpenAI chat completion.
        /// Available Chat Completion models can be found at https://platform.openai.com/docs/models.
        /// </summary>
        public string? ModelId { get; set; }
        public string? ApiKey { get; set; }
        public string? OrgId { get; set; }
    }

    internal class AzureOpenAIConfig
    {
        public string? DeploymentName { get; set; }
        public string? Endpoint { get; set; }
        public string? ApiKey { get; set; }
    }

    internal class AzureAdConfig
    {
        public string? ClientId { get; set; }
        public string? TenantId { get; set; }
        public string? ClientSecret { get; set; }
        public bool InteractiveBrowserAuthentication { get; set; }
        public string? InteractiveBrowserRedirectUri { get; set; }
    }
}
