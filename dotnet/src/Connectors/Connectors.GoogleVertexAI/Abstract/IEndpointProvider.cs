// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;

/// <summary>
/// Represents an interface for retrieving various endpoints related to gemini api.
/// </summary>
internal interface IEndpointProvider
{
    /// <summary>
    /// Returns the URI endpoint for text generation using the specified model ID.
    /// </summary>
    /// <param name="modelId">The ID of the model to be used for text generation.</param>
    /// <returns>The URI of the text generation endpoint.</returns>
    Uri GetTextGenerationEndpoint(string modelId);

    /// <summary>
    /// Returns the URI endpoint for streaming text generation using the specified model ID.
    /// </summary>
    /// <param name="modelId">The ID of the model to be used for text generation.</param>
    /// <returns>The URI of the stream text generation endpoint.</returns>
    Uri GetStreamTextGenerationEndpoint(string modelId);

    /// <summary>
    /// Returns the URI endpoint for chat completion based on the provided model ID.
    /// </summary>
    /// <param name="modelId">The ID of the model to be used for text generation.</param>
    /// <returns>The URI endpoint for chat completion.</returns>
    Uri GetChatCompletionEndpoint(string modelId);

    /// <summary>
    /// Returns the completion URI endpoint for the Stream Chat API using the provided model ID.
    /// </summary>
    /// <param name="modelId">The ID of the model to be used for text generation.</param>
    /// <returns>The URI endpoint for streaming chat completion.</returns>
    Uri GetStreamChatCompletionEndpoint(string modelId);

    /// <summary>
    /// Constructs the endpoint URL for fetching embeddings for a specific model.
    /// </summary>
    /// <param name="modelId">The ID of the model to be used for fetching embeddings.</param>
    /// <returns>The URI endpoint for fetching embeddings.</returns>
    Uri GetEmbeddingsEndpoint(string modelId);

    /// <summary>
    /// Constructs the count tokens endpoint URI for a given model ID.
    /// </summary>
    /// <param name="modelId">The ID of the model.</param>
    /// <returns>The count tokens endpoint URI.</returns>
    Uri GetCountTokensEndpoint(string modelId);
}
