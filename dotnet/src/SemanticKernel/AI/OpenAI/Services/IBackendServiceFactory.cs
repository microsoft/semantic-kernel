// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Configuration;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

/// <summary>
/// Interface for a backend service factory.
/// </summary>
public interface IBackendServiceFactory
{
    /// <summary>
    /// Creates an embedding generator.
    /// </summary>
    /// <param name="config">The backend config.</param>
    /// <returns>An instance of the embedding generator.</returns>
    IEmbeddingGenerator<string, float> CreateEmbeddingGenerator(IBackendConfig config);

    /// <summary>
    /// Creates text completion client.
    /// </summary>
    /// <param name="config">The backend config.</param>
    /// <param name="functionDescription">The function description.</param>
    /// <returns>An instance of the text completion client.</returns>
    ITextCompletionClient CreateTextCompletionClient(IBackendConfig config, string functionDescription);
}
