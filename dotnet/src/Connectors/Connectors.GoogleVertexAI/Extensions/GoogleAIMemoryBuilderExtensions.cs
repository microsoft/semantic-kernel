// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure GoogleAI connector.
/// </summary>
public static class GoogleAIMemoryBuilderExtensions
{
    /// <summary>
    /// Add GoogleAI embeddings generation service to the memory builder.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="apiKey">The API key for authentication Gemini API.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated memory builder.</returns>
    public static MemoryBuilder WithGoogleAIEmbeddingGeneration(
        this MemoryBuilder builder,
        string modelId,
        string apiKey,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);

        return builder.WithTextEmbeddingGeneration((loggerFactory, builderHttpClient) =>
            new GoogleAITextEmbeddingGenerationService(
                model: modelId,
                apiKey: apiKey,
                httpClient: HttpClientProvider.GetHttpClient(httpClient ?? builderHttpClient),
                loggerFactory: loggerFactory));
    }
}
