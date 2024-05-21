// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Azure;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.TextGeneration;
using Microsoft.SemanticKernel.TextToAudio;
using Microsoft.SemanticKernel.TextToImage;

#pragma warning disable CA2000 // Dispose objects before losing scope
#pragma warning disable IDE0039 // Use local function

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for <see cref="IServiceCollection"/> and related classes to configure OpenAI and Azure OpenAI connectors.
/// </summary>
public static class OpenAIServiceCollectionExtensions
{
    #region Text Completion

    /// <summary>
    /// Adds an Azure OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAITextGeneration(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        {
            var client = CreateAzureOpenAIClient(endpoint, new AzureKeyCredential(apiKey), httpClient ?? serviceProvider.GetService<HttpClient>());
            return new AzureOpenAITextGenerationService(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        });

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAITextGeneration(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        {
            var client = CreateAzureOpenAIClient(endpoint, new AzureKeyCredential(apiKey), serviceProvider.GetService<HttpClient>());
            return new AzureOpenAITextGenerationService(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        });
    }

    /// <summary>
    /// Adds an Azure OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAITextGeneration(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        {
            var client = CreateAzureOpenAIClient(endpoint, credentials, httpClient ?? serviceProvider.GetService<HttpClient>());
            return new AzureOpenAITextGenerationService(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        });

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAITextGeneration(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        {
            var client = CreateAzureOpenAIClient(endpoint, credentials, serviceProvider.GetService<HttpClient>());
            return new AzureOpenAITextGenerationService(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        });
    }

    /// <summary>
    /// Adds an Azure OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAITextGeneration(
        this IKernelBuilder builder,
        string deploymentName,
        OpenAIClient? openAIClient = null,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);

        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextGenerationService(
                deploymentName,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                modelId,
                serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAITextGeneration(
        this IServiceCollection services,
        string deploymentName,
        OpenAIClient? openAIClient = null,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextGenerationService(
                deploymentName,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                modelId,
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds an Azure OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextGeneration(
        this IKernelBuilder builder,
        AzureOpenAIConfig config,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.AzureIdentity:
                builder.AddAzureOpenAITextGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: new DefaultAzureCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient);
                break;

            case AzureOpenAIConfig.AuthTypes.ManualTokenCredential:
                builder.AddAzureOpenAITextGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: config.GetTokenCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient);
                break;

            case AzureOpenAIConfig.AuthTypes.APIKey:
                builder.AddAzureOpenAITextGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextGeneration(
        this IServiceCollection services,
        AzureOpenAIConfig config)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.AzureIdentity:
                services.AddAzureOpenAITextGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: new DefaultAzureCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment);
                break;

            case AzureOpenAIConfig.AuthTypes.ManualTokenCredential:
                services.AddAzureOpenAITextGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: config.GetTokenCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment);
                break;

            case AzureOpenAIConfig.AuthTypes.APIKey:
                services.AddAzureOpenAITextGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    serviceId: config.ServiceId,
                    modelId: config.Deployment);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return services;
    }

    /// <summary>
    /// Adds an OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddOpenAITextGeneration(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new OpenAITextGenerationService(
                modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }

    /// <summary>
    /// Adds an OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAITextGeneration(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new OpenAITextGenerationService(
                modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds an OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddOpenAITextGeneration(
        this IKernelBuilder builder,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);

        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new OpenAITextGenerationService(
                modelId,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }

    /// <summary>
    /// Adds an OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAITextGeneration(
        this IServiceCollection services,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new OpenAITextGenerationService(
                modelId,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds an OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAITextGeneration(
        this IKernelBuilder builder,
        OpenAIConfig config,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        return builder.AddOpenAITextGeneration(
            modelId: config.TextModel,
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId,
            httpClient: httpClient);
    }

    /// <summary>
    /// Adds an OpenAI text generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAITextGeneration(
        this IServiceCollection services,
        OpenAIConfig config,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        return services.AddOpenAITextGeneration(
            modelId: config.TextModel,
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId);
    }

    #endregion

    #region Text Embedding

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        int? dimensions = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                apiKey,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                apiKey,
                modelId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        int? dimensions = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credential);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                credential,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credential);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                credential,
                modelId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        string deploymentName,
        OpenAIClient? openAIClient = null,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                modelId,
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        string deploymentName,
        OpenAIClient? openAIClient = null,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                modelId,
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        AzureOpenAIConfig config,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.AzureIdentity:
                builder.AddAzureOpenAITextEmbeddingGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credential: new DefaultAzureCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient,
                    dimensions: config.EmbeddingDimensions);
                break;

            case AzureOpenAIConfig.AuthTypes.ManualTokenCredential:
                builder.AddAzureOpenAITextEmbeddingGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credential: config.GetTokenCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient,
                    dimensions: config.EmbeddingDimensions);
                break;

            case AzureOpenAIConfig.AuthTypes.APIKey:
                builder.AddAzureOpenAITextEmbeddingGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient,
                    dimensions: config.EmbeddingDimensions);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        AzureOpenAIConfig config)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.AzureIdentity:
                services.AddAzureOpenAITextEmbeddingGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credential: new DefaultAzureCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    dimensions: config.EmbeddingDimensions);
                break;

            case AzureOpenAIConfig.AuthTypes.ManualTokenCredential:
                services.AddAzureOpenAITextEmbeddingGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credential: config.GetTokenCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    dimensions: config.EmbeddingDimensions);
                break;

            case AzureOpenAIConfig.AuthTypes.APIKey:
                services.AddAzureOpenAITextEmbeddingGeneration(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    dimensions: config.EmbeddingDimensions);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return services;
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null,
        int? dimensions = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new OpenAITextEmbeddingGenerationService(
                modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));

        return builder;
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        int? dimensions = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new OpenAITextEmbeddingGenerationService(
                modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null,
        int? dimensions = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new OpenAITextEmbeddingGenerationService(
                modelId,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));

        return builder;
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The OpenAI model id.</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null,
        int? dimensions = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new OpenAITextEmbeddingGenerationService(
                modelId,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        OpenAIConfig config,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        return builder.AddOpenAITextEmbeddingGeneration(
            modelId: config.EmbeddingModel,
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId,
            httpClient: httpClient,
            dimensions: config.EmbeddingDimensions);
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        OpenAIConfig config,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        return services.AddOpenAITextEmbeddingGeneration(
            modelId: config.EmbeddingModel,
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId,
            dimensions: config.EmbeddingDimensions);
    }

    #endregion

    #region Chat Completion

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAIChatCompletion(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
        {
            OpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                new AzureKeyCredential(apiKey),
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider));

            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAIChatCompletion(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
        {
            OpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                new AzureKeyCredential(apiKey),
                HttpClientProvider.GetHttpClient(serviceProvider));

            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAIChatCompletion(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
        {
            OpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                credentials,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider));

            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAIChatCompletion(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
        {
            OpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                credentials,
                HttpClientProvider.GetHttpClient(serviceProvider));

            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAIChatCompletion(
        this IKernelBuilder builder,
        string deploymentName,
        OpenAIClient? openAIClient = null,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
            new(deploymentName, openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(), modelId, serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAIChatCompletion(
        this IServiceCollection services,
        string deploymentName,
        OpenAIClient? openAIClient = null,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
            new(deploymentName, openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(), modelId, serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion with data service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance.</param>
    /// <param name="config">Required configuration for Azure OpenAI chat completion with data.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    /// <remarks>
    /// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
    /// </remarks>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAIChatCompletion(
        this IKernelBuilder builder,
        AzureOpenAIChatCompletionWithDataConfig config,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionWithDataService> factory = (serviceProvider, _) =>
            new(config,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion with data service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance.</param>
    /// <param name="config">Required configuration for Azure OpenAI chat completion with data.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    /// <remarks>
    /// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
    /// </remarks>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAIChatCompletion(
        this IServiceCollection services,
        AzureOpenAIChatCompletionWithDataConfig config,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionWithDataService> factory = (serviceProvider, _) =>
            new(config,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion with data service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    /// <remarks>
    /// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
    /// </remarks>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAIChatCompletion(
        this IKernelBuilder builder,
        AzureOpenAIConfig config,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.AzureIdentity:
                builder.AddAzureOpenAIChatCompletion(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: new DefaultAzureCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient);
                break;

            case AzureOpenAIConfig.AuthTypes.ManualTokenCredential:
                builder.AddAzureOpenAIChatCompletion(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: config.GetTokenCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient);
                break;

            case AzureOpenAIConfig.AuthTypes.APIKey:
                builder.AddAzureOpenAIChatCompletion(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion with data service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    /// <remarks>
    /// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
    /// </remarks>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAIChatCompletion(
        this IServiceCollection services,
        AzureOpenAIConfig config)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.AzureIdentity:
                services.AddAzureOpenAIChatCompletion(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: new DefaultAzureCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment);
                break;

            case AzureOpenAIConfig.AuthTypes.ManualTokenCredential:
                services.AddAzureOpenAIChatCompletion(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: config.GetTokenCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment);
                break;

            case AzureOpenAIConfig.AuthTypes.APIKey:
                services.AddAzureOpenAIChatCompletion(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    serviceId: config.ServiceId,
                    modelId: config.Deployment);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return services;
    }

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddOpenAIChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, OpenAIChatCompletionService> factory = (serviceProvider, _) =>
            new(modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAIChatCompletion(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, OpenAIChatCompletionService> factory = (serviceProvider, _) =>
            new(modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model id.</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddOpenAIChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);

        Func<IServiceProvider, object?, OpenAIChatCompletionService> factory = (serviceProvider, _) =>
            new(modelId, openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(), serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model id.</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAIChatCompletion(
        this IServiceCollection services,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        Func<IServiceProvider, object?, OpenAIChatCompletionService> factory = (serviceProvider, _) =>
            new(modelId, openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(), serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Custom OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="endpoint">A Custom Message API compatible endpoint.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAIChatCompletion(
        this IServiceCollection services,
        string modelId,
        Uri endpoint,
        string? apiKey = null,
        string? orgId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        Func<IServiceProvider, object?, OpenAIChatCompletionService> factory = (serviceProvider, _) =>
            new(modelId,
                endpoint,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Custom Endpoint OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="endpoint">Custom OpenAI Compatible Message API endpoint.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAIChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        Uri endpoint,
        string? apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);

        Func<IServiceProvider, object?, OpenAIChatCompletionService> factory = (serviceProvider, _) =>
            new(modelId: modelId,
                apiKey: apiKey,
                endpoint: endpoint,
                organization: orgId,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the Custom OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAIChatCompletion(
        this IServiceCollection services,
        OpenAIConfig config,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        return services.AddOpenAIChatCompletion(
            modelId: config.TextModel,
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId);
    }

    /// <summary>
    /// Adds the Custom Endpoint OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAIChatCompletion(
        this IKernelBuilder builder,
        OpenAIConfig config,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        return builder.AddOpenAIChatCompletion(
            modelId: config.TextModel,
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId,
            httpClient: httpClient);
    }

    #endregion

    #region Images

    /// <summary>
    /// Add the  Azure OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name.</param>
    /// <param name="endpoint">Azure OpenAI deployment URL.</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="apiVersion">Azure OpenAI API version.</param>
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
    /// Add the  Azure OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name.</param>
    /// <param name="endpoint">Azure OpenAI deployment URL.</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="apiVersion">Azure OpenAI API version.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextToImage(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? modelId = null,
        string? serviceId = null,
        string? apiVersion = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        builder.Services.AddKeyedSingleton<ITextToImageService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToImageService(
                deploymentName,
                endpoint,
                credentials,
                modelId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                apiVersion));

        return builder;
    }

    /// <summary>
    /// Add the  Azure OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name.</param>
    /// <param name="endpoint">Azure OpenAI deployment URL.</param>
    /// <param name="apiKey">Azure OpenAI API key.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="apiVersion">Azure OpenAI API version.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextToImage(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? modelId = null,
        string? serviceId = null,
        string? apiVersion = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton<ITextToImageService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToImageService(
                deploymentName,
                endpoint,
                apiKey,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                apiVersion));

        return builder;
    }

    /// <summary>
    /// Add the  Azure OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name.</param>
    /// <param name="endpoint">Azure OpenAI deployment URL.</param>
    /// <param name="apiKey">Azure OpenAI API key.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="apiVersion">Azure OpenAI API version.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextToImage(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
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
    /// Add the OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAITextToImage(
        this IKernelBuilder builder,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton<ITextToImageService>(serviceId, (serviceProvider, _) =>
            new OpenAITextToImageService(
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }

    /// <summary>
    /// Add the OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAITextToImage(
        this IServiceCollection services,
        string apiKey,
        string? orgId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextToImageService>(serviceId, (serviceProvider, _) =>
            new OpenAITextToImageService(
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Add the OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAITextToImage(
        this IKernelBuilder builder,
        OpenAIConfig config,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        return builder.AddOpenAITextToImage(
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId,
            httpClient: httpClient);
    }

    /// <summary>
    /// Add the OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAITextToImage(
        this IServiceCollection services,
        OpenAIConfig config,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        return services.AddOpenAITextToImage(
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId);
    }

    /// <summary>
    /// Add the OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name.</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextToImage(
        this IServiceCollection services,
        string deploymentName,
        OpenAIClient? openAIClient = null,
        string? modelId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);

        return services.AddKeyedSingleton<ITextToImageService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToImageService(
                deploymentName,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                modelId,
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Add the OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name.</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextToImage(
        this IKernelBuilder builder,
        string deploymentName,
        OpenAIClient? openAIClient = null,
        string? modelId = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);

        builder.Services.AddKeyedSingleton<ITextToImageService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToImageService(
                deploymentName,
                openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(),
                modelId,
                serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }

    /// <summary>
    /// Add the OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <param name="apiVersion">Azure OpenAI API version.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextToImage(
        this IServiceCollection services,
        AzureOpenAIConfig config,
        string? apiVersion = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.AzureIdentity:
                services.AddAzureOpenAITextToImage(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: new DefaultAzureCredential(),
                    modelId: config.Deployment,
                    serviceId: config.ServiceId,
                    apiVersion: apiVersion);
                break;

            case AzureOpenAIConfig.AuthTypes.ManualTokenCredential:
                services.AddAzureOpenAITextToImage(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: config.GetTokenCredential(),
                    modelId: config.Deployment,
                    serviceId: config.ServiceId,
                    apiVersion: apiVersion);
                break;

            case AzureOpenAIConfig.AuthTypes.APIKey:
                services.AddAzureOpenAITextToImage(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    apiVersion: apiVersion);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return services;
    }

    /// <summary>
    /// Add the OpenAI Dall-E text to image service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <param name="apiVersion">Azure OpenAI API version.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextToImage(
        this IKernelBuilder builder,
        AzureOpenAIConfig config,
        string? apiVersion = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.AzureIdentity:
                builder.AddAzureOpenAITextToImage(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: new DefaultAzureCredential(),
                    modelId: config.Deployment,
                    serviceId: config.ServiceId,
                    apiVersion: apiVersion);
                break;

            case AzureOpenAIConfig.AuthTypes.ManualTokenCredential:
                builder.AddAzureOpenAITextToImage(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: config.GetTokenCredential(),
                    modelId: config.Deployment,
                    serviceId: config.ServiceId,
                    apiVersion: apiVersion);
                break;

            case AzureOpenAIConfig.AuthTypes.APIKey:
                builder.AddAzureOpenAITextToImage(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    modelId: config.Deployment,
                    serviceId: config.ServiceId,
                    apiVersion: apiVersion,
                    httpClient: httpClient);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return builder;
    }

    #endregion

    #region Files

    /// <summary>
    /// Add the OpenAI file service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAIFiles(
        this IKernelBuilder builder,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton(serviceId, (serviceProvider, _) =>
            new OpenAIFileService(
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }

    /// <summary>
    /// Add the OpenAI file service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAIFiles(
        this IServiceCollection services,
        string apiKey,
        string? orgId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(apiKey);

        services.AddKeyedSingleton(serviceId, (serviceProvider, _) =>
            new OpenAIFileService(
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));

        return services;
    }

    /// <summary>
    /// Add the OpenAI file service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAIFiles(
        this IKernelBuilder builder,
        OpenAIConfig config,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        return builder.AddOpenAIFiles(
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId,
            httpClient: httpClient);
    }

    /// <summary>
    /// Add the OpenAI file service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAIFiles(
        this IServiceCollection services,
        OpenAIConfig config,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        return services.AddOpenAIFiles(
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId);
    }

    /// <summary>
    /// Add the OpenAI file service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="endpoint">Azure OpenAI deployment URL.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="version">The API version to target.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAIFiles(
        this IKernelBuilder builder,
        string endpoint,
        string apiKey,
        string? orgId = null,
        string? version = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton(serviceId, (serviceProvider, _) =>
            new OpenAIFileService(
                new Uri(endpoint),
                apiKey,
                orgId,
                version,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }

    /// <summary>
    /// Add the OpenAI file service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="endpoint">Azure OpenAI deployment URL.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="version">The API version to target.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAIFiles(
        this IServiceCollection services,
        string endpoint,
        string apiKey,
        string? orgId = null,
        string? version = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(apiKey);

        services.AddKeyedSingleton(serviceId, (serviceProvider, _) =>
            new OpenAIFileService(
                new Uri(endpoint),
                apiKey,
                orgId,
                version,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));

        return services;
    }

    /// <summary>
    /// Add the OpenAI file service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="version">The API version to target.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAIFiles(
        this IKernelBuilder builder,
        AzureOpenAIConfig config,
        string? orgId = null,
        string? version = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.APIKey:
                builder.AddAzureOpenAIFiles(
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    orgId: orgId,
                    version: version,
                    serviceId: config.ServiceId,
                    httpClient: httpClient);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return builder;
    }

    /// <summary>
    /// Add the OpenAI file service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="version">The API version to target.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAIFiles(
        this IServiceCollection services,
        AzureOpenAIConfig config,
        string? orgId = null,
        string? version = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.APIKey:
                services.AddAzureOpenAIFiles(
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    orgId: orgId,
                    version: version,
                    serviceId: config.ServiceId);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return services;
    }

    #endregion

    #region Text-to-Audio

    /// <summary>
    /// Adds the Azure OpenAI text-to-audio service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name.</param>
    /// <param name="endpoint">Azure OpenAI deployment URL.</param>
    /// <param name="apiKey">Azure OpenAI API key.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IKernelBuilder AddAzureOpenAITextToAudio(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton<ITextToAudioService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToAudioService(
                deploymentName,
                endpoint,
                apiKey,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI text-to-audio service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name.</param>
    /// <param name="endpoint">Azure OpenAI deployment URL.</param>
    /// <param name="apiKey">Azure OpenAI API key.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IServiceCollection AddAzureOpenAITextToAudio(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null)
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
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds the Azure OpenAI text-to-audio service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextToAudio(
        this IKernelBuilder builder,
        AzureOpenAIConfig config,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.APIKey:
                builder.AddAzureOpenAITextToAudio(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI text-to-audio service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAITextToAudio(
        this IServiceCollection services,
        AzureOpenAIConfig config,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.APIKey:
                services.AddAzureOpenAITextToAudio(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return services;
    }

    /// <summary>
    /// Adds the OpenAI text-to-audio service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IKernelBuilder AddOpenAITextToAudio(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton<ITextToAudioService>(serviceId, (serviceProvider, _) =>
            new OpenAITextToAudioService(
                modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }

    /// <summary>
    /// Adds the OpenAI text-to-audio service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IServiceCollection AddOpenAITextToAudio(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextToAudioService>(serviceId, (serviceProvider, _) =>
            new OpenAITextToAudioService(
                modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds the OpenAI text-to-audio service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAITextToAudio(
        this IKernelBuilder builder,
        OpenAIConfig config,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        return builder.AddOpenAITextToAudio(
            modelId: config.TextModel,
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId,
            httpClient: httpClient);
    }

    /// <summary>
    /// Adds the OpenAI text-to-audio service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAITextToAudio(
        this IServiceCollection services,
        OpenAIConfig config,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        return services.AddOpenAITextToAudio(
            modelId: config.TextModel,
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId);
    }

    #endregion

    #region Audio-to-Text

    /// <summary>
    /// Adds the Azure OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IKernelBuilder AddAzureOpenAIAudioToText(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
        {
            OpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                new AzureKeyCredential(apiKey),
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider));
            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        builder.Services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IServiceCollection AddAzureOpenAIAudioToText(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
        {
            OpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                new AzureKeyCredential(apiKey),
                HttpClientProvider.GetHttpClient(serviceProvider));
            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Azure OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IKernelBuilder AddAzureOpenAIAudioToText(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
        {
            OpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                credentials,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider));
            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        builder.Services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IServiceCollection AddAzureOpenAIAudioToText(
        this IServiceCollection services,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
        {
            OpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                credentials,
                HttpClientProvider.GetHttpClient(serviceProvider));
            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Azure OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IKernelBuilder AddAzureOpenAIAudioToText(
        this IKernelBuilder builder,
        string deploymentName,
        OpenAIClient? openAIClient = null,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
            new(deploymentName, openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(), modelId, serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IServiceCollection AddAzureOpenAIAudioToText(
        this IServiceCollection services,
        string deploymentName,
        OpenAIClient? openAIClient = null,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
            new(deploymentName, openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(), modelId, serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Azure OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAIAudioToText(
        this IKernelBuilder builder,
        AzureOpenAIConfig config,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.AzureIdentity:
                builder.AddAzureOpenAIAudioToText(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: new DefaultAzureCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient);
                break;

            case AzureOpenAIConfig.AuthTypes.ManualTokenCredential:
                builder.AddAzureOpenAIAudioToText(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: config.GetTokenCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient);
                break;

            case AzureOpenAIConfig.AuthTypes.APIKey:
                builder.AddAzureOpenAIAudioToText(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    serviceId: config.ServiceId,
                    modelId: config.Deployment,
                    httpClient: httpClient);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return builder;
    }

    /// <summary>
    /// Adds the Azure OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for Azure OpenAI.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddAzureOpenAIAudioToText(
        this IServiceCollection services,
        AzureOpenAIConfig config)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        switch (config.Auth)
        {
            case AzureOpenAIConfig.AuthTypes.AzureIdentity:
                services.AddAzureOpenAIAudioToText(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: new DefaultAzureCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment);
                break;

            case AzureOpenAIConfig.AuthTypes.ManualTokenCredential:
                services.AddAzureOpenAIAudioToText(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    credentials: config.GetTokenCredential(),
                    serviceId: config.ServiceId,
                    modelId: config.Deployment);
                break;

            case AzureOpenAIConfig.AuthTypes.APIKey:
                services.AddAzureOpenAIAudioToText(
                    deploymentName: config.Deployment,
                    endpoint: config.Endpoint,
                    apiKey: config.APIKey,
                    serviceId: config.ServiceId,
                    modelId: config.Deployment);
                break;

            default:
                throw new NotImplementedException($"Azure OpenAI auth type '{config.Auth}' not available");
        }

        return services;
    }

    /// <summary>
    /// Adds the OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IKernelBuilder AddOpenAIAudioToText(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, OpenAIAudioToTextService> factory = (serviceProvider, _) =>
            new(modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IServiceCollection AddOpenAIAudioToText(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, OpenAIAudioToTextService> factory = (serviceProvider, _) =>
            new(modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model id.</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IKernelBuilder AddOpenAIAudioToText(
        this IKernelBuilder builder,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);

        Func<IServiceProvider, object?, OpenAIAudioToTextService> factory = (serviceProvider, _) =>
            new(modelId, openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(), serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model id.</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0001")]
    public static IServiceCollection AddOpenAIAudioToText(
        this IServiceCollection services,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        Func<IServiceProvider, object?, OpenAIAudioToTextService> factory = (serviceProvider, _) =>
            new(modelId, openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(), serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAIAudioToText(
        this IKernelBuilder builder,
        OpenAIConfig config,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        config.Validate();

        return builder.AddOpenAIAudioToText(
            modelId: config.TextModel,
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId,
            httpClient: httpClient);
    }

    /// <summary>
    /// Adds the OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="config">Required configuration for OpenAI.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAIAudioToText(
        this IServiceCollection services,
        OpenAIConfig config,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(config);

        config.Validate();

        return services.AddOpenAIAudioToText(
            modelId: config.TextModel,
            apiKey: config.APIKey,
            orgId: config.OrgId,
            serviceId: serviceId);
    }

    #endregion

    private static OpenAIClient CreateAzureOpenAIClient(string endpoint, AzureKeyCredential credentials, HttpClient? httpClient) =>
        new(new Uri(endpoint), credentials, ClientCore.GetOpenAIClientOptions(httpClient));

    private static OpenAIClient CreateAzureOpenAIClient(string endpoint, TokenCredential credentials, HttpClient? httpClient) =>
        new(new Uri(endpoint), credentials, ClientCore.GetOpenAIClientOptions(httpClient));
}
