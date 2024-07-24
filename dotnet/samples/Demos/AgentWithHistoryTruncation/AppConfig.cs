// Copyright (c) Microsoft. All rights reserved.

internal sealed class AppConfig
{
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

    internal bool IsAzureOpenAIConfigured => this.AzureOpenAI?.ChatDeploymentName is not null;

    /// <summary>
    /// Ensures that the configuration is valid.
    /// </summary>
    internal void Validate()
    {
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
        public string? ChatDeploymentName { get; set; }

        /// <summary>
        /// Endpoint of the Azure OpenAI resource.
        /// </summary>
        public string? Endpoint { get; set; }

        /// <summary>
        /// ApiKey to use for the Azure OpenAI chat completion.
        /// </summary>
        public string? ApiKey { get; set; }
    }
}
