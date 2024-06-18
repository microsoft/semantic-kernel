// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using OpenAI;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Sponsor class for OpenAI text embedding kernel builder extensions.
/// </summary>
public static class OpenAIKernelBuilderExtensions
{
    #region Text Embedding
    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="options">Options for the OpenAI text embeddings service.</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        OpenAITextEmbeddingGenerationOptions options,
        OpenAIClient? openAIClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(options.ModelId);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(options.ServiceId, (serviceProvider, _) =>
            new OpenAITextEmbeddingGenerationService(
                options,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>()));

        return builder;
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="options">Options for the OpenAI text embeddings service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        OpenAIClientTextEmbeddingGenerationOptions options,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(options.ModelId);
        Verify.NotNullOrWhiteSpace(options.ApiKey);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(options.ServiceId, (serviceProvider, _) =>
            new OpenAITextEmbeddingGenerationService(
                options,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider)));

        return builder;
    }
    #endregion
}
