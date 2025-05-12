// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using OpenAI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Sponsor extensions class for <see cref="IServiceCollection"/>.
/// </summary>
public static partial class OpenAIServiceCollectionExtensions
{
    #region Text Embedding
    /// <summary>
    /// Adds the <see cref="IEmbeddingGenerator{TInput, TEmbedding}"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAIEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? orgId = null,
        int? dimensions = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
#pragma warning disable CS0618 // Type or member is obsolete
            new OpenAITextEmbeddingGenerationService(
                modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(), dimensions)
            .AsEmbeddingGenerator());
#pragma warning restore CS0618 // Type or member is obsolete
    }

    /// <summary>
    /// Adds the <see cref="IEmbeddingGenerator{TInput, TEmbedding}"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The OpenAI model id.</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAIEmbeddingGenerator(this IServiceCollection services,
        string modelId,
        OpenAIClient? openAIClient = null,
        int? dimensions = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

#pragma warning disable CS0618 // Type or member is obsolete
        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
            new OpenAITextEmbeddingGenerationService(
                modelId,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions)
            .AsEmbeddingGenerator());
#pragma warning restore CS0618 // Type or member is obsolete
    }
    #endregion
}
