// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure OpenAI and AzureOpenAI connectors.
/// </summary>
public static class OpenAIMemoryBuilderExtensions
{
    /// <summary>
    /// Adds the OpenAI text embeddings service.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance</param>
    /// <param name="options">Options for the OpenAI text embeddings service.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    [Experimental("SKEXP0010")]
    public static MemoryBuilder WithOpenAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        OpenAIClientTextEmbeddingGenerationConfig options,
        HttpClient? httpClient = null)
    {
        return builder.WithTextEmbeddingGeneration((loggerFactory, builderHttpClient) =>
            new OpenAITextEmbeddingGenerationService(
                options,
                HttpClientProvider.GetHttpClient(httpClient ?? builderHttpClient)));
    }
}
