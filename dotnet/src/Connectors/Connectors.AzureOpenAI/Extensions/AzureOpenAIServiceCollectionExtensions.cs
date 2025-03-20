// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.TextGeneration;
using Microsoft.SemanticKernel.TextToAudio;
using Microsoft.SemanticKernel.TextToImage;

#pragma warning disable IDE0039 // Use local function

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for <see cref="IServiceCollection"/> to configure Azure OpenAI connectors.
/// </summary>
public static class AzureOpenAIServiceCollectionExtensions
{
    #region Chat Completion

    /// <summary>
    /// Adds the <see cref="AzureOpenAIChatCompletionService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAIChatCompletion(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        string? apiVersion = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
        {
            AzureOpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                new ApiKeyCredential(apiKey),
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                apiVersion);

            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAIChatCompletionService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAIChatCompletion(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        string? modelId = null,
        string? apiVersion = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
        {
            AzureOpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                credentials,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                apiVersion);

            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAIChatCompletionService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="azureOpenAIClient"><see cref="AzureOpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAIChatCompletion(
        this IServiceCollection services,
        string deploymentName,
        AzureOpenAIClient? azureOpenAIClient = null,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
            new(deploymentName, azureOpenAIClient ?? serviceProvider.GetRequiredService<AzureOpenAIClient>(), modelId, serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return services;
    }

    #endregion

    #region Text Embedding

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
    public static IServiceCollection AddAzureOpenAITextEmbeddingGeneration(
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

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                apiKey,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions,
                apiVersion));
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
    public static IServiceCollection AddAzureOpenAITextEmbeddingGeneration(
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

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                credential,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions,
                apiVersion));
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
    public static IServiceCollection AddAzureOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        string deploymentName,
        AzureOpenAIClient? azureOpenAIClient = null,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                azureOpenAIClient ?? serviceProvider.GetRequiredService<AzureOpenAIClient>(),
                modelId,
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));
    }

    #endregion

    #region Text-to-Audio

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextToAudioService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextToAudio(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        string? apiVersion = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextToAudioService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToAudioService(
                deploymentName,
                endpoint,
                apiKey,
                modelId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                apiVersion));
    }

    #endregion

    #region Images

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextToImageService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextToImage(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? modelId = null,
        string? serviceId = null,
        string? apiVersion = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        return services.AddKeyedSingleton<ITextToImageService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToImageService(
                deploymentName,
                endpoint,
                credentials,
                modelId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                apiVersion));
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextToImageService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="maxRetryCount">Maximum number of attempts to retrieve the text to image operation result.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextToImage(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        int maxRetryCount = 5,
        string? apiVersion = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextToImageService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToImageService(
                deploymentName,
                endpoint,
                apiKey,
                modelId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                apiVersion));
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextToImageService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient"><see cref="AzureOpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextToImage(
        this IServiceCollection services,
        string deploymentName,
        AzureOpenAIClient? openAIClient = null,
        string? modelId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);

        return services.AddKeyedSingleton<ITextToImageService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToImageService(
                deploymentName,
                openAIClient ?? serviceProvider.GetRequiredService<AzureOpenAIClient>(),
                modelId,
                serviceProvider.GetService<ILoggerFactory>()));
    }

    #endregion

    #region Audio-to-Text

    /// <summary>
    /// Adds the <see cref="AzureOpenAIAudioToTextService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAIAudioToText(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        string? apiVersion = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
        {
            AzureOpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                new ApiKeyCredential(apiKey),
                HttpClientProvider.GetHttpClient(serviceProvider),
                apiVersion);
            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAIAudioToTextService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAIAudioToText(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        string? modelId = null,
        string? apiVersion = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
        {
            AzureOpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                credentials,
                HttpClientProvider.GetHttpClient(serviceProvider),
                apiVersion);
            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAIAudioToTextService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient"><see cref="AzureOpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAIAudioToText(
        this IServiceCollection services,
        string deploymentName,
        AzureOpenAIClient? openAIClient = null,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
            new(deploymentName, openAIClient ?? serviceProvider.GetRequiredService<AzureOpenAIClient>(), modelId, serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return services;
    }

    #endregion

    private static AzureOpenAIClient CreateAzureOpenAIClient(string endpoint, ApiKeyCredential credentials, HttpClient? httpClient, string? apiVersion) =>
        new(new Uri(endpoint), credentials, AzureClientCore.GetAzureOpenAIClientOptions(httpClient, apiVersion));

    private static AzureOpenAIClient CreateAzureOpenAIClient(string endpoint, TokenCredential credentials, HttpClient? httpClient, string? apiVersion) =>
        new(new Uri(endpoint), credentials, AzureClientCore.GetAzureOpenAIClientOptions(httpClient, apiVersion));
}
