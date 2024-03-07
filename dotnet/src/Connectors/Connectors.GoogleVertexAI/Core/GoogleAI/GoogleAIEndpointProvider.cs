// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Provides a collection of endpoints for the Gemini API.
/// </summary>
internal sealed class GoogleAIEndpointProvider : IEndpointProvider
{
    private readonly string _apiKey;

    /// <summary>
    /// Initializes a new instance of the GeminiEndpoints class with the specified API key.
    /// </summary>
    /// <param name="apiKey">The API key to use for authentication.</param>
    public GoogleAIEndpointProvider(string apiKey)
    {
        this._apiKey = apiKey;
    }

    /// <summary>
    /// Gets the base endpoint for the Gemini API.
    /// </summary>
    public static Uri BaseEndpoint { get; } = new("https://generativelanguage.googleapis.com/v1beta/");

    /// <summary>
    /// Gets the endpoint URI for accessing the models in the Gemini API.
    /// </summary>
    public static Uri ModelsEndpoint { get; } = new(BaseEndpoint, "models/");

    /// <inheritdoc />
    public Uri GetGeminiTextGenerationEndpoint(string modelId)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:generateContent?key={this._apiKey}");

    /// <inheritdoc />
    public Uri GetGeminiStreamTextGenerationEndpoint(string modelId)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:streamGenerateContent?key={this._apiKey}&alt=sse");

    /// <inheritdoc />
    public Uri GetGeminiChatCompletionEndpoint(string modelId)
        => this.GetGeminiTextGenerationEndpoint(modelId);

    /// <inheritdoc />
    public Uri GetGeminiStreamChatCompletionEndpoint(string modelId)
        => this.GetGeminiStreamTextGenerationEndpoint(modelId);

    /// <inheritdoc />
    public Uri GetEmbeddingsEndpoint(string modelId)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:batchEmbedContents?key={this._apiKey}");

    /// <inheritdoc />
    public Uri GetCountTokensEndpoint(string modelId)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:countTokens?key={this._apiKey}");
}
