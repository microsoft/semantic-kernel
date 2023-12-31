#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Core;

/// <summary>
/// Provides a collection of endpoints for the Gemini API.
/// </summary>
public static class GeminiEndpoints
{
    /// <summary>
    /// Gets the base endpoint for the Gemini API.
    /// </summary>
    public static Uri BaseEndpoint { get; } = new("https://generativelanguage.googleapis.com/v1beta/");

    /// <summary>
    /// Gets the endpoint URI for accessing the models in the Gemini API.
    /// </summary>
    public static Uri ModelsEndpoint { get; } = new(BaseEndpoint, "models/");

    /// <summary>
    /// Returns the URI endpoint for text generation using the specified model ID and API key.
    /// </summary>
    /// <param name="modelId">The ID of the model to be used for text generation.</param>
    /// <param name="apiKey">The API key to access the text generation service.</param>
    /// <returns>The URI of the text generation endpoint.</returns>
    public static Uri GetTextGenerationEndpoint(string modelId, string apiKey)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:generateContent?key={apiKey}");

    /// <summary>
    /// Returns the URI endpoint for streaming text generation using the specified model ID and API key.
    /// </summary>
    /// <param name="modelId">The ID of the model to be used for text generation.</param>
    /// <param name="apiKey">The API key to access the text generation service.</param>
    /// <returns>The URI of the stream text generation endpoint.</returns>
    public static Uri GetStreamTextGenerationEndpoint(string modelId, string apiKey)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:streamGenerateContent?key={apiKey}");

    /// <summary>
    /// Returns the URI endpoint for chat completion based on the provided model ID and API key.
    /// </summary>
    /// <param name="modelId">The ID of the model to be used for text generation.</param>
    /// <param name="apiKey">The API key to access the text generation service.</param>
    /// <returns>The URI endpoint for chat completion.</returns>
    public static Uri GetChatCompletionEndpoint(string modelId, string apiKey)
        => GetTextGenerationEndpoint(modelId, apiKey);

    /// <summary>
    /// Returns the completion URI endpoint for the Stream Chat API using the provided model ID and API key.
    /// </summary>
    /// <param name="modelId">The ID of the model to be used for text generation.</param>
    /// <param name="apiKey">The API key to access the text generation service.</param>
    /// <returns>The URI endpoint for streaming chat completion.</returns>
    public static Uri GetStreamChatCompletionEndpoint(string modelId, string apiKey)
        => GetStreamTextGenerationEndpoint(modelId, apiKey);

    /// <summary>
    /// Constructs the endpoint URL for fetching embeddings for a specific model.
    /// </summary>
    /// <param name="modelId">The ID of the model to be used for fetching embeddings.</param>
    /// <param name="apiKey">The API key to access the embeddings generation service.</param>
    /// <returns>The URI endpoint for fetching embeddings.</returns>
    public static Uri GetEmbeddingsEndpoint(string modelId, string apiKey)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:batchEmbedContents?key={apiKey}");
}
