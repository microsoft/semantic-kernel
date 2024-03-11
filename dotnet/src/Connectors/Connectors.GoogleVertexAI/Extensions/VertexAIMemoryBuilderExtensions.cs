// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure VertexAI connector.
/// </summary>
public static class VertexAIMemoryBuilderExtensions
{
    /// <summary>
    /// Add VertexAI embeddings generation service to the memory builder.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bearerKey">The Bearer Key for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated memory builder.</returns>
    public static MemoryBuilder WithVertexAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(modelId);
        Verify.NotNull(bearerKey);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        return builder.WithTextEmbeddingGeneration((loggerFactory, builderHttpClient) =>
            new VertexAITextEmbeddingGenerationService(
                model: modelId,
                bearerKey: bearerKey,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(httpClient ?? builderHttpClient),
                loggerFactory: loggerFactory));
    }
}
