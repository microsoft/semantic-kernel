// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Provides extension methods for <see cref="IServiceCollection"/> to configure Azure OpenAI connectors.
/// </summary>
public static class AzureOpenAIServiceCollectionExtensions
{
    /// <summary>
    /// Adds the <see cref="AzureOpenAITextEmbeddingGenerationService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAIEmbeddingGenerator(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null,
        string? apiVersion = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

#pragma warning disable CS0618 // Type or member is obsolete
        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                apiKey,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(), dimensions,
                apiVersion)
            .AsEmbeddingGenerator());
#pragma warning restore CS0618 // Type or member is obsolete
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextEmbeddingGenerationService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAIEmbeddingGenerator(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null,
        string? apiVersion = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(credential);

#pragma warning disable CS0618 // Type or member is obsolete
        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                credential,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions,
                apiVersion
                )
            .AsEmbeddingGenerator());
#pragma warning restore CS0618 // Type or member is obsolete
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextEmbeddingGenerationService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="azureOpenAIClient"><see cref="AzureOpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAIEmbeddingGenerator(
        this IServiceCollection services,
        string deploymentName,
        AzureOpenAIClient? azureOpenAIClient = null,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null)
    {
        Verify.NotNull(services);

#pragma warning disable CS0618 // Type or member is obsolete
        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                azureOpenAIClient ?? serviceProvider.GetRequiredService<AzureOpenAIClient>(),
                modelId,
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions)
            .AsEmbeddingGenerator());
#pragma warning restore CS0618 // Type or member is obsolete
    }
}
