// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Provides a collection of endpoints for the Gemini Vertex AI API.
/// </summary>
internal sealed class VertexAIEndpointProvider : IEndpointProvider
{
    /// <summary>
    /// Initializes a new instance of the GeminiEndpoints class with the specified API key.
    /// </summary>
    /// <param name="configuration">Vertex AI configuration.</param>
    public VertexAIEndpointProvider(VertexAIConfiguration configuration)
    {
        this.BaseEndpoint = new Uri($"https://{configuration.Location}-aiplatform.googleapis.com/v1/projects/" +
                                    $"{configuration.ProjectId}/locations/{configuration.Location}/publishers/google/");
        this.ModelsEndpoint = new Uri(this.BaseEndpoint, "models/");
    }

    /// <summary>
    /// Gets the base endpoint for the Gemini API.
    /// </summary>
    public Uri BaseEndpoint { get; }

    /// <summary>
    /// Gets the endpoint URI for accessing the models in the Gemini API.
    /// </summary>
    public Uri ModelsEndpoint { get; }

    /// <inheritdoc />
    public Uri GetGeminiTextGenerationEndpoint(string modelId)
        => new($"{this.ModelsEndpoint.AbsoluteUri}{modelId}:generateContent");

    /// <inheritdoc />
    public Uri GetGeminiStreamTextGenerationEndpoint(string modelId)
        => new($"{this.ModelsEndpoint.AbsoluteUri}{modelId}:streamGenerateContent?alt=sse");

    /// <inheritdoc />
    public Uri GetGeminiChatCompletionEndpoint(string modelId)
        => this.GetGeminiTextGenerationEndpoint(modelId);

    /// <inheritdoc />
    public Uri GetGeminiStreamChatCompletionEndpoint(string modelId)
        => this.GetGeminiStreamTextGenerationEndpoint(modelId);

    /// <inheritdoc />
    public Uri GetEmbeddingsEndpoint(string modelId)
        => new($"{this.ModelsEndpoint.AbsoluteUri}{modelId}:predict");

    /// <inheritdoc />
    public Uri GetCountTokensEndpoint(string modelId)
        => new($"{this.ModelsEndpoint.AbsoluteUri}{modelId}:countTokens");
}
