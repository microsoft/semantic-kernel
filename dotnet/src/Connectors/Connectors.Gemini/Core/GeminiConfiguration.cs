#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

/// <summary>
/// Represents the configuration for the Gemini API.
/// </summary>
internal sealed class GeminiConfiguration
{
    /// <summary>
    /// Gets the API key used for authentication.
    /// </summary>
    public string ApiKey { get; }

    /// <summary>
    /// Model ID to use for generating text and chat completion.
    /// </summary>
    public string? ModelId { get; init; }

    /// <summary>
    /// Model ID to use for embeddings generation.
    /// </summary>
    public string? EmbeddingModelId { get; init; }

    public GeminiConfiguration(string apiKey)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        this.ApiKey = apiKey;
    }
}
