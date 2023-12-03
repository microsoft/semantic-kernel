// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Azure;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;

#pragma warning disable CA2000 // Dispose objects before losing scope
#pragma warning disable IDE0039 // Use local function

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for the <see cref="IServiceCollection"/> class to configure OpenAI and Azure OpenAI connectors.
/// </summary>
public static class OpenAIServiceCollectionExtensions
{
    #region Text Completion

    /// <summary>
    /// Adds an Azure OpenAI text completion service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithAzureOpenAITextCompletion(
        this KernelBuilder builder,
        string deploymentName,
        string modelId,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
            {
                var client = CreateAzureOpenAIClient(deploymentName, endpoint, new AzureKeyCredential(apiKey), httpClient ?? serviceProvider.GetService<HttpClient>());
                return new AzureOpenAITextCompletion(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
            });
        });
    }

    /// <summary>
    /// Adds an Azure OpenAI text completion service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAITextCompletion(
        this IServiceCollection services,
        string deploymentName,
        string modelId,
        string endpoint,
        string apiKey,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
        {
            var client = CreateAzureOpenAIClient(deploymentName, endpoint, new AzureKeyCredential(apiKey), serviceProvider.GetService<HttpClient>());
            return new AzureOpenAITextCompletion(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        });
    }

    /// <summary>
    /// Adds an Azure OpenAI text completion service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithAzureOpenAITextCompletion(
        this KernelBuilder builder,
        string deploymentName,
        string modelId,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
            {
                var client = CreateAzureOpenAIClient(deploymentName, endpoint, credentials, httpClient ?? serviceProvider.GetService<HttpClient>());
                return new AzureOpenAITextCompletion(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
            });
        });
    }

    /// <summary>
    /// Adds an Azure OpenAI text completion service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAITextCompletion(
        this IServiceCollection services,
        string deploymentName,
        string modelId,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        return services.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
        {
            var client = CreateAzureOpenAIClient(deploymentName, endpoint, credentials, serviceProvider.GetService<HttpClient>());
            return new AzureOpenAITextCompletion(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        });
    }

    /// <summary>
    /// Adds an Azure OpenAI text completion service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithAzureOpenAITextCompletion(
        this KernelBuilder builder,
        string deploymentName,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
                new AzureOpenAITextCompletion(
                    deploymentName,
                    openAIClient,
                    modelId,
                    serviceProvider.GetService<ILoggerFactory>()));
        });
    }

    /// <summary>
    /// Adds an Azure OpenAI text completion service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAITextCompletion(
        this IServiceCollection services,
        string deploymentName,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        return services.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextCompletion(
                deploymentName,
                openAIClient,
                modelId,
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds an OpenAI text completion service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithOpenAITextCompletion(
        this KernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
                new OpenAITextCompletion(
                    modelId,
                    apiKey,
                    orgId,
                    HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>()));
        });
    }

    /// <summary>
    /// Adds an OpenAI text completion service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAITextCompletion(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
            new OpenAITextCompletion(
                modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds an OpenAI text completion service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithOpenAITextCompletion(
        this KernelBuilder builder,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
                new OpenAITextCompletion(
                    modelId,
                    openAIClient,
                    serviceProvider.GetService<ILoggerFactory>()));
        });
    }

    /// <summary>
    /// Adds an OpenAI text completion service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAITextCompletion(this IServiceCollection services,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        return services.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
            new OpenAITextCompletion(
                modelId,
                openAIClient,
                serviceProvider.GetService<ILoggerFactory>()));
    }

    #endregion

    #region Text Embedding

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0011")]
    public static KernelBuilder WithAzureOpenAITextEmbeddingGeneration(
        this KernelBuilder builder,
        string deploymentName,
        string modelId,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
                new AzureOpenAITextEmbeddingGeneration(
                    deploymentName,
                    modelId,
                    endpoint,
                    apiKey,
                    HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>()));
        });
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0011")]
    public static IServiceCollection AddAzureOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        string deploymentName,
        string modelId,
        string endpoint,
        string apiKey,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGeneration(
                deploymentName,
                modelId,
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0011")]
    public static KernelBuilder WithAzureOpenAITextEmbeddingGeneration(
        this KernelBuilder builder,
        string deploymentName,
        string modelId,
        string endpoint,
        TokenCredential credential,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credential);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
                new AzureOpenAITextEmbeddingGeneration(
                    deploymentName,
                    modelId,
                    endpoint,
                    credential,
                    HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>()));
        });
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0011")]
    public static IServiceCollection AddAzureOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        string deploymentName,
        string modelId,
        string endpoint,
        TokenCredential credential,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credential);

        return services.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGeneration(
                deploymentName,
                modelId,
                endpoint,
                credential,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0011")]
    public static KernelBuilder WithAzureOpenAITextEmbeddingGeneration(
        this KernelBuilder builder,
        string deploymentName,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
                new AzureOpenAITextEmbeddingGeneration(
                    deploymentName,
                    modelId,
                    openAIClient,
                    serviceProvider.GetService<ILoggerFactory>()));
        });
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0011")]
    public static IServiceCollection AddAzureOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        string deploymentName,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        return services.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGeneration(
                deploymentName,
                modelId,
                openAIClient,
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0011")]
    public static KernelBuilder WithOpenAITextEmbeddingGeneration(
        this KernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
                new OpenAITextEmbeddingGeneration(
                    modelId,
                    apiKey,
                    orgId,
                    HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>()));
        });
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0011")]
    public static IServiceCollection AddOpenAITextEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
            new OpenAITextEmbeddingGeneration(
                modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0011")]
    public static KernelBuilder WithOpenAITextEmbeddingGeneration(
        this KernelBuilder builder,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
                new OpenAITextEmbeddingGeneration(
                    modelId,
                    openAIClient,
                    serviceProvider.GetService<ILoggerFactory>()));
        });
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The OpenAI model id.</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0011")]
    public static IServiceCollection AddOpenAITextEmbeddingGeneration(this IServiceCollection services,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        return services.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
            new OpenAITextEmbeddingGeneration(
                modelId,
                openAIClient,
                serviceProvider.GetService<ILoggerFactory>()));
    }

    #endregion

    #region Chat Completion

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithAzureOpenAIChatCompletion(
        this KernelBuilder builder,
        string deploymentName,
        string modelId,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        return builder.WithServices(c =>
        {
            Func<IServiceProvider, object?, AzureOpenAIChatCompletion> factory = (serviceProvider, _) =>
            {
                OpenAIClient client = CreateAzureOpenAIClient(
                    deploymentName,
                    endpoint,
                    new AzureKeyCredential(apiKey),
                    HttpClientProvider.GetHttpClient(httpClient, serviceProvider));

                return new(deploymentName, modelId, client, serviceProvider.GetService<ILoggerFactory>());
            };

            c.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
            c.AddKeyedSingleton<ITextCompletion>(serviceId, factory);
        });
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAIChatCompletion(
        this IServiceCollection services,
        string deploymentName,
        string modelId,
        string endpoint,
        string apiKey,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletion> factory = (serviceProvider, _) =>
        {
            OpenAIClient client = CreateAzureOpenAIClient(
                deploymentName,
                endpoint,
                new AzureKeyCredential(apiKey),
                HttpClientProvider.GetHttpClient(serviceProvider));

            return new(deploymentName, modelId, client, serviceProvider.GetService<ILoggerFactory>());
        };

        services.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
        services.AddKeyedSingleton<ITextCompletion>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithAzureOpenAIChatCompletion(
        this KernelBuilder builder,
        string deploymentName,
        string modelId,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        return builder.WithServices(c =>
        {
            Func<IServiceProvider, object?, AzureOpenAIChatCompletion> factory = (serviceProvider, _) =>
            {
                OpenAIClient client = CreateAzureOpenAIClient(
                    deploymentName,
                    endpoint,
                    credentials,
                    HttpClientProvider.GetHttpClient(httpClient, serviceProvider));

                return new(deploymentName, modelId, client, serviceProvider.GetService<ILoggerFactory>());
            };

            c.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
            c.AddKeyedSingleton<ITextCompletion>(serviceId, factory);
        });
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAIChatCompletion(
        this IServiceCollection services,
        string deploymentName,
        string modelId,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletion> factory = (serviceProvider, _) =>
        {
            OpenAIClient client = CreateAzureOpenAIClient(
                deploymentName,
                endpoint,
                credentials,
                HttpClientProvider.GetHttpClient(serviceProvider));

            return new(deploymentName, modelId, client, serviceProvider.GetService<ILoggerFactory>());
        };

        services.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
        services.AddKeyedSingleton<ITextCompletion>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithAzureOpenAIChatCompletion(
        this KernelBuilder builder,
        string deploymentName,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        return builder.WithServices(c =>
        {
            Func<IServiceProvider, object?, AzureOpenAIChatCompletion> factory = (serviceProvider, _) =>
                new(deploymentName, modelId, openAIClient, serviceProvider.GetService<ILoggerFactory>());

            c.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
            c.AddKeyedSingleton<ITextCompletion>(serviceId, factory);
        });
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureOpenAIChatCompletion(
        this IServiceCollection services,
        string deploymentName,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletion> factory = (serviceProvider, _) =>
            new(deploymentName, modelId, openAIClient, serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
        services.AddKeyedSingleton<ITextCompletion>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the Azure OpenAI chat completion with data service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="config">Required configuration for Azure OpenAI chat completion with data.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    /// <remarks>
    /// More information: <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/use-your-data-quickstart"/>
    /// </remarks>
    [Experimental("SKEXP0010")]
    public static KernelBuilder WithAzureOpenAIChatCompletion(
        this KernelBuilder builder,
        AzureOpenAIChatCompletionWithDataConfig config,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(config);

        return builder.WithServices(c =>
        {
            Func<IServiceProvider, object?, AzureOpenAIChatCompletionWithData> factory = (serviceProvider, _) =>
                new(config,
                    HttpClientProvider.GetHttpClient(serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>());

            c.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
            c.AddKeyedSingleton<ITextCompletion>(serviceId, factory);
        });
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

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionWithData> factory = (serviceProvider, _) =>
            new(config,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
        services.AddKeyedSingleton<ITextCompletion>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithOpenAIChatCompletion(
        this KernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        return builder.WithServices(c =>
        {
            Func<IServiceProvider, object?, OpenAIChatCompletion> factory = (serviceProvider, _) =>
                new(modelId,
                    apiKey,
                    orgId,
                    HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>());

            c.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
            c.AddKeyedSingleton<ITextCompletion>(serviceId, factory);
        });
    }

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
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

        Func<IServiceProvider, object?, OpenAIChatCompletion> factory = (serviceProvider, _) =>
            new(modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
        services.AddKeyedSingleton<ITextCompletion>(serviceId, factory);

        return services;
    }

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model id</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithOpenAIChatCompletion(
        this KernelBuilder builder,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        return builder.WithServices(c =>
        {
            Func<IServiceProvider, object?, OpenAIChatCompletion> factory = (serviceProvider, _) =>
                new(modelId, openAIClient, serviceProvider.GetService<ILoggerFactory>());

            c.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
            c.AddKeyedSingleton<ITextCompletion>(serviceId, factory);
        });
    }

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model id</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAIChatCompletion(this IServiceCollection services,
        string modelId,
        OpenAIClient openAIClient,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        Func<IServiceProvider, object?, OpenAIChatCompletion> factory = (serviceProvider, _) =>
            new(modelId, openAIClient, serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<IChatCompletion>(serviceId, factory);
        services.AddKeyedSingleton<ITextCompletion>(serviceId, factory);

        return services;
    }

    #endregion

    #region Images

    /// <summary>
    /// Add the  Azure OpenAI DallE image generation service to the list
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="maxRetryCount">Maximum number of attempts to retrieve the image generation operation result.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0012")]
    public static KernelBuilder WithAzureOpenAIImageGeneration(
        this KernelBuilder builder,
        string endpoint,
        string modelId,
        string apiKey,
        string? serviceId = null,
        int maxRetryCount = 5,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<IImageGeneration>(serviceId, (serviceProvider, _) =>
                new AzureOpenAIImageGeneration(
                    endpoint,
                    modelId,
                    apiKey,
                    HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>(),
                    maxRetryCount));
        });
    }

    /// <summary>
    /// Add the  Azure OpenAI DallE image generation service to the list
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="maxRetryCount">Maximum number of attempts to retrieve the image generation operation result.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0012")]
    public static IServiceCollection AddAzureOpenAIImageGeneration(
        this IServiceCollection services,
        string endpoint,
        string modelId,
        string apiKey,
        string? serviceId = null,
        int maxRetryCount = 5)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<IImageGeneration>(serviceId, (serviceProvider, _) =>
            new AzureOpenAIImageGeneration(
                endpoint,
                modelId,
                apiKey,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                maxRetryCount));
    }

    /// <summary>
    /// Add the OpenAI Dall-E image generation service to the list
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0012")]
    public static KernelBuilder WithOpenAIImageGeneration(
        this KernelBuilder builder,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(apiKey);

        return builder.WithServices(c =>
        {
            c.AddKeyedSingleton<IImageGeneration>(serviceId, (serviceProvider, _) =>
                new OpenAIImageGeneration(
                    apiKey,
                    orgId,
                    HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>()));
        });
    }

    /// <summary>
    /// Add the OpenAI Dall-E image generation service to the list
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0012")]
    public static IServiceCollection AddOpenAIImageGeneration(this IServiceCollection services,
        string apiKey,
        string? orgId = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<IImageGeneration>(serviceId, (serviceProvider, _) =>
            new OpenAIImageGeneration(
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    #endregion

    private static OpenAIClient CreateAzureOpenAIClient(string deploymentName, string endpoint, AzureKeyCredential credentials, HttpClient? httpClient) =>
        new(new Uri(endpoint), credentials, ClientCore.GetOpenAIClientOptions(httpClient));

    private static OpenAIClient CreateAzureOpenAIClient(string deploymentName, string endpoint, TokenCredential credentials, HttpClient? httpClient) =>
        new(new Uri(endpoint), credentials, ClientCore.GetOpenAIClientOptions(httpClient));
}
