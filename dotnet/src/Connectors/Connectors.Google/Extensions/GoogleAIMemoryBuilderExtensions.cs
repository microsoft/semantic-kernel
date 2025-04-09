// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Google;
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
    /// <param name="apiVersion">The version of the Google API.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <param name="dimensions">The optional number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    /// <returns>The updated memory builder.</returns>
    public static MemoryBuilder WithGoogleAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        string modelId,
        string apiKey,
        GoogleAIVersion apiVersion = GoogleAIVersion.V1_Beta,
        HttpClient? httpClient = null,
        int? dimensions = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);

        return builder.WithTextEmbeddingGeneration((loggerFactory, builderHttpClient) =>
            new GoogleAITextEmbeddingGenerationService(
                modelId: modelId,
                apiKey: apiKey,
                apiVersion: apiVersion,
                httpClient: HttpClientProvider.GetHttpClient(httpClient ?? builderHttpClient),
                loggerFactory: loggerFactory,
                dimensions: dimensions));
    }
}
