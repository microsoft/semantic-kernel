// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using OpenAI;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Sponsor class for OpenAI text embedding service collection extensions.
/// </summary>
public static class TextEmbeddingServiceCollectionExtensions
{
    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="options">Options for the OpenAI text embeddings service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        OpenAIClientTextEmbeddingGenerationOptions options)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(options.ModelId);
        Verify.NotNullOrWhiteSpace(options.ApiKey);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(options.ServiceId, (serviceProvider, _) =>
            new OpenAITextEmbeddingGenerationService(
                options,
                HttpClientProvider.GetHttpClient(serviceProvider)));
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="options">Options for the OpenAI text embeddings service.</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAITextEmbeddingGeneration(this IServiceCollection services,
        OpenAITextEmbeddingGenerationOptions options,
        OpenAIClient? openAIClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(options.ModelId);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(options.ServiceId, (serviceProvider, _) =>
            new OpenAITextEmbeddingGenerationService(
                options,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>()));
    }
}
