#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using Microsoft.SemanticKernel.Connectors.Gemini.Abstract;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core.VertexAI;

/// <summary>
/// Provides a collection of endpoints for the Gemini Vertex AI API.
/// </summary>
internal sealed class VertexAIGeminiEndpointProvider : IEndpointProvider
{
    private readonly VertexAIConfiguration _configuration;

    /// <summary>
    /// Initializes a new instance of the GeminiEndpoints class with the specified API key.
    /// </summary>
    /// <param name="configuration">Vertex AI configuration.</param>
    public VertexAIGeminiEndpointProvider(VertexAIConfiguration configuration)
    {
        this._configuration = configuration;
    }

    /// <summary>
    /// Gets the base endpoint for the Gemini API.
    /// </summary>
    public Uri BaseEndpoint => new($"https://{this._configuration.Location}-aiplatform.googleapis.com/v1/projects/{this._configuration.ProjectId}/locations/{this._configuration.Location}/publishers/google/");

    /// <summary>
    /// Gets the endpoint URI for accessing the models in the Gemini API.
    /// </summary>
    public Uri ModelsEndpoint => new(this.BaseEndpoint, "models/");

    /// <inheritdoc />
    public Uri GetTextGenerationEndpoint(string modelId)
        => new($"{this.ModelsEndpoint.AbsoluteUri}{modelId}:generateContent");

    /// <inheritdoc />
    public Uri GetStreamTextGenerationEndpoint(string modelId)
        => new($"{this.ModelsEndpoint.AbsoluteUri}{modelId}:streamGenerateContent");

    /// <inheritdoc />
    public Uri GetChatCompletionEndpoint(string modelId)
        => this.GetTextGenerationEndpoint(modelId);

    /// <inheritdoc />
    public Uri GetStreamChatCompletionEndpoint(string modelId)
        => this.GetStreamTextGenerationEndpoint(modelId);

    /// <inheritdoc />
    public Uri GetEmbeddingsEndpoint(string modelId)
        => new($"{this.ModelsEndpoint.AbsoluteUri}{modelId}:batchEmbedContents");

    /// <inheritdoc />
    public Uri GetCountTokensEndpoint(string modelId)
        => new($"{this.ModelsEndpoint.AbsoluteUri}{modelId}:countTokens");
}
