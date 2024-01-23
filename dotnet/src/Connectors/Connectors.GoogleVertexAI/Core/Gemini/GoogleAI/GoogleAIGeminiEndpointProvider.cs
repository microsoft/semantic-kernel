// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Provides a collection of endpoints for the Gemini API.
/// </summary>
internal sealed class GoogleAIGeminiEndpointProvider : IEndpointProvider
{
    private readonly string _apiKey;

    /// <summary>
    /// Initializes a new instance of the GeminiEndpoints class with the specified API key.
    /// </summary>
    /// <param name="apiKey">The API key to use for authentication.</param>
    public GoogleAIGeminiEndpointProvider(string apiKey)
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
    public Uri GetTextGenerationEndpoint(string modelId)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:generateContent?key={this._apiKey}");

    /// <inheritdoc />
    public Uri GetStreamTextGenerationEndpoint(string modelId)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:streamGenerateContent?key={this._apiKey}");

    /// <inheritdoc />
    public Uri GetChatCompletionEndpoint(string modelId)
        => this.GetTextGenerationEndpoint(modelId);

    /// <inheritdoc />
    public Uri GetStreamChatCompletionEndpoint(string modelId)
        => this.GetStreamTextGenerationEndpoint(modelId);

    /// <inheritdoc />
    public Uri GetEmbeddingsEndpoint(string modelId)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:batchEmbedContents?key={this._apiKey}");

    /// <inheritdoc />
    public Uri GetCountTokensEndpoint(string modelId)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:countTokens?key={this._apiKey}");
}
