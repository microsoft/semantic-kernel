// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel;

public abstract class AzureOpenAIConfig
{
    /// <summary>
    /// Azure OpenAI endpoint URL.
    /// </summary>
    public string Endpoint { get; set; } = string.Empty;

    /// <summary>
    /// Azure OpenAI deployment name.
    /// </summary>
    public string Deployment { get; set; } = string.Empty;

    /// <summary>
    /// The number of dimensions output embeddings should have.
    /// Only supported in "text-embedding-3" and later models developed with
    /// MRL, see https://arxiv.org/abs/2205.13147
    /// </summary>
    public int? EmbeddingDimensions { get; set; }

    /// <summary>
    /// Azure OpenAI API version.
    /// </summary>
    public string ApiVersion { get; set; } = string.Empty;

    /// <summary>
    /// A local identifier for the given AI service.
    /// </summary>
    public string ServiceId { get; set; } = string.Empty;

    /// <summary>
    /// Verify that the current state is valid.
    /// </summary>
    public virtual void Validate()
    {
        if (string.IsNullOrWhiteSpace(this.Endpoint))
        {
            throw new ConfigurationException($"Azure OpenAI: {nameof(this.Endpoint)} is empty");
        }

        if (!this.Endpoint.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
        {
            throw new ConfigurationException($"Azure OpenAI: {nameof(this.Endpoint)} must start with https://");
        }

        if (string.IsNullOrWhiteSpace(this.Deployment))
        {
            throw new ConfigurationException($"Azure OpenAI: {nameof(this.Deployment)} (deployment name) is empty");
        }

        if (this.EmbeddingDimensions is < 1)
        {
            throw new ConfigurationException($"Azure OpenAI: {nameof(this.EmbeddingDimensions)} cannot be less than 1");
        }
    }
}
