// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure.Core;

namespace Microsoft.SemanticKernel;

public class AzureOpenAIConfig
{
    private TokenCredential? _tokenCredential;

    public enum AuthTypes
    {
        Unknown = -1,
        AzureIdentity,
        APIKey,
        ManualTokenCredential,
    }

    public enum APITypes
    {
        Unknown = -1,
        TextCompletion,
        ChatCompletion,
        ImageGeneration,
        EmbeddingGeneration,
    }

    /// <summary>
    /// OpenAI API type, e.g. text completion, chat completion, image generation, etc.
    /// </summary>
    public APITypes APIType { get; set; } = APITypes.ChatCompletion;

    /// <summary>
    /// Azure authentication type.
    /// </summary>
    public AuthTypes Auth { get; set; }

    /// <summary>
    /// Azure OpenAI endpoint URL.
    /// </summary>
    public string Endpoint { get; set; } = string.Empty;

    /// <summary>
    /// Azure OpenAI deployment name.
    /// </summary>
    public string Deployment { get; set; } = string.Empty;

    /// <summary>
    /// The max number of tokens supported by model deployed.
    /// </summary>
    public int MaxTokenTotal { get; set; } = 8191;

    /// <summary>
    /// API key, required if Auth == APIKey.
    /// </summary>
    public string APIKey { get; set; } = string.Empty;

    /// <summary>
    /// The number of dimensions output embeddings should have.
    /// Only supported in "text-embedding-3" and later models developed with
    /// MRL, see https://arxiv.org/abs/2205.13147
    /// </summary>
    public int? EmbeddingDimensions { get; set; }

    /// <summary>
    /// Set credentials manually from code.
    /// </summary>
    /// <param name="credential">Token credentials</param>
    public void SetCredential(TokenCredential credential)
    {
        this.Auth = AuthTypes.ManualTokenCredential;
        this._tokenCredential = credential;
    }

    /// <summary>
    /// Fetch the credentials passed manually from code.
    /// </summary>
    public TokenCredential GetTokenCredential()
    {
        return this._tokenCredential
               ?? throw new ConfigurationException($"Azure OpenAI: {nameof(this._tokenCredential)} not defined");
    }

    /// <summary>
    /// Verify that the current state is valid.
    /// </summary>
    public void Validate()
    {
        if (this.Auth == AuthTypes.Unknown)
        {
            throw new ConfigurationException($"Azure OpenAI: {nameof(this.Auth)} (authentication type) is not defined");
        }

        if (this.Auth == AuthTypes.APIKey && string.IsNullOrWhiteSpace(this.APIKey))
        {
            throw new ConfigurationException($"Azure OpenAI: {nameof(this.APIKey)} is empty");
        }

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

        if (this.MaxTokenTotal < 1)
        {
            throw new ConfigurationException($"Azure OpenAI: {nameof(this.MaxTokenTotal)} cannot be less than 1");
        }

        if (this.EmbeddingDimensions is < 1)
        {
            throw new ConfigurationException($"Azure OpenAI: {nameof(this.EmbeddingDimensions)} cannot be less than 1");
        }
    }
}
