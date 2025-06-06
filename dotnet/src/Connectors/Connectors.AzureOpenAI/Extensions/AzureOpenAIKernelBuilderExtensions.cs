// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.AI;
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
/// Provides extension methods for <see cref="IKernelBuilder"/> to configure Azure OpenAI connectors.
/// </summary>
public static partial class AzureOpenAIKernelBuilderExtensions
{
    #region Chat Client

    /// <summary>
    /// Adds an Azure OpenAI <see cref="IChatClient"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAIChatClient(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        string? apiVersion = null,
        HttpClient? httpClient = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAzureOpenAIChatClient(
            deploymentName,
            endpoint,
            apiKey,
            serviceId,
            modelId,
            apiVersion,
            httpClient,
            openTelemetrySourceName,
            openTelemetryConfig);

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI <see cref="IChatClient"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAIChatClient(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        string? modelId = null,
        string? apiVersion = null,
        HttpClient? httpClient = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAzureOpenAIChatClient(
            deploymentName,
            endpoint,
            credentials,
            serviceId,
            modelId,
            apiVersion,
            httpClient,
            openTelemetrySourceName,
            openTelemetryConfig);

        return builder;
    }

    /// <summary>
    /// Adds an Azure OpenAI <see cref="IChatClient"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="azureOpenAIClient"><see cref="AzureOpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAIChatClient(
        this IKernelBuilder builder,
        string deploymentName,
        AzureOpenAIClient? azureOpenAIClient = null,
        string? serviceId = null,
        string? modelId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAzureOpenAIChatClient(
            deploymentName,
            azureOpenAIClient,
            serviceId,
            modelId,
            openTelemetrySourceName,
            openTelemetryConfig);

        return builder;
    }

    #endregion

    #region Chat Completion

    /// <summary>
    /// Adds the <see cref="AzureOpenAIChatCompletionService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAIChatCompletion(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        string? apiVersion = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
        {
            AzureOpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                new ApiKeyCredential(apiKey),
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider), apiVersion);

            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAIChatCompletionService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAIChatCompletion(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        string? apiVersion = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
        {
            AzureOpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                credentials,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider), apiVersion);

            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAIChatCompletionService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="azureOpenAIClient"><see cref="AzureOpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddAzureOpenAIChatCompletion(
        this IKernelBuilder builder,
        string deploymentName,
        AzureOpenAIClient? azureOpenAIClient = null,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);

        Func<IServiceProvider, object?, AzureOpenAIChatCompletionService> factory = (serviceProvider, _) =>
            new(deploymentName, azureOpenAIClient ?? serviceProvider.GetRequiredService<AzureOpenAIClient>(), modelId, serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, factory);

        return builder;
    }

    #endregion

    #region Text Embedding

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextEmbeddingGenerationService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    [Obsolete("Use AddAzureOpenAIEmbeddingGenerator instead.")]
    public static IKernelBuilder AddAzureOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        int? dimensions = null,
        string? apiVersion = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                apiKey,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions,
                apiVersion));

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextEmbeddingGenerationService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    [Obsolete("Use AddAzureOpenAIEmbeddingGenerator instead.")]
    public static IKernelBuilder AddAzureOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        int? dimensions = null,
        string? apiVersion = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(credential);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                credential,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions,
                apiVersion));

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextEmbeddingGenerationService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="azureOpenAIClient"><see cref="AzureOpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    [Obsolete("Use AddAzureOpenAIEmbeddingGenerator instead.")]
    public static IKernelBuilder AddAzureOpenAITextEmbeddingGeneration(
        this IKernelBuilder builder,
        string deploymentName,
        AzureOpenAIClient? azureOpenAIClient = null,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                azureOpenAIClient ?? serviceProvider.GetRequiredService<AzureOpenAIClient>(),
                modelId,
                serviceProvider.GetService<ILoggerFactory>(),
                dimensions));

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextToAudioService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextToAudio(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        string? apiVersion = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credential);

        builder.Services.AddKeyedSingleton<ITextToAudioService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToAudioService(
                deploymentName,
                endpoint,
                credential,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                apiVersion));

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextEmbeddingGenerationService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="IEmbeddingGenerator{String, Embedding}"/> instance.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAIEmbeddingGenerator(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null,
        string? apiVersion = null,
        HttpClient? httpClient = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryEmbeddingGenerator<string, Embedding<float>>>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAzureOpenAIEmbeddingGenerator(
            deploymentName,
            endpoint,
            apiKey,
            serviceId,
            modelId,
            dimensions,
            apiVersion,
            httpClient,
            openTelemetrySourceName,
            openTelemetryConfig);

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextEmbeddingGenerationService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="IEmbeddingGenerator{String, Embedding}"/> instance.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAIEmbeddingGenerator(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null,
        string? apiVersion = null,
        HttpClient? httpClient = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryEmbeddingGenerator<string, Embedding<float>>>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(credential);

        builder.Services.AddAzureOpenAIEmbeddingGenerator(
            deploymentName,
            endpoint,
            credential,
            serviceId,
            modelId,
            dimensions,
            apiVersion,
            httpClient,
            openTelemetrySourceName,
            openTelemetryConfig);

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextEmbeddingGenerationService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="azureOpenAIClient"><see cref="AzureOpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="IEmbeddingGenerator{String, Embedding}"/> instance.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAIEmbeddingGenerator(
        this IKernelBuilder builder,
        string deploymentName,
        AzureOpenAIClient? azureOpenAIClient = null,
        string? serviceId = null,
        string? modelId = null,
        int? dimensions = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryEmbeddingGenerator<string, Embedding<float>>>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAzureOpenAIEmbeddingGenerator(
            deploymentName,
            azureOpenAIClient,
            serviceId,
            modelId,
            dimensions,
            openTelemetrySourceName,
            openTelemetryConfig);

        return builder;
    }

    #endregion

    #region Text-to-Audio

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextToAudioService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextToAudio(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        string? apiVersion = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton<ITextToAudioService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToAudioService(
                deploymentName,
                endpoint,
                apiKey,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>(),
                apiVersion));

        return builder;
    }

    #endregion

    #region Images

    /// <summary>
    /// Adds the <see cref="AzureOpenAITextToImageService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="apiVersion">Azure OpenAI API version</param>
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
    /// Adds the <see cref="AzureOpenAITextToImageService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="apiVersion">Azure OpenAI API version</param>
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
    /// Adds the <see cref="AzureOpenAITextToImageService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="azureOpenAIClient"><see cref="AzureOpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAITextToImage(
        this IKernelBuilder builder,
        string deploymentName,
        AzureOpenAIClient? azureOpenAIClient = null,
        string? modelId = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);

        builder.Services.AddKeyedSingleton<ITextToImageService>(serviceId, (serviceProvider, _) =>
            new AzureOpenAITextToImageService(
                deploymentName,
                azureOpenAIClient ?? serviceProvider.GetRequiredService<AzureOpenAIClient>(),
                modelId,
                serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }

    #endregion

    #region Audio-to-Text

    /// <summary>
    /// Adds the <see cref="AzureOpenAIAudioToTextService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAIAudioToText(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        string? apiVersion = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
        {
            AzureOpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                new ApiKeyCredential(apiKey),
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                apiVersion);

            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        builder.Services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAIAudioToTextService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAIAudioToText(
        this IKernelBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credentials,
        string? serviceId = null,
        string? modelId = null,
        HttpClient? httpClient = null,
        string? apiVersion = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.NotNull(credentials);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
        {
            AzureOpenAIClient client = CreateAzureOpenAIClient(
                endpoint,
                credentials,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                apiVersion);

            return new(deploymentName, client, modelId, serviceProvider.GetService<ILoggerFactory>());
        };

        builder.Services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="AzureOpenAIAudioToTextService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient"><see cref="AzureOpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="modelId">Model identifier, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddAzureOpenAIAudioToText(
        this IKernelBuilder builder,
        string deploymentName,
        AzureOpenAIClient? openAIClient = null,
        string? serviceId = null,
        string? modelId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(deploymentName);

        Func<IServiceProvider, object?, AzureOpenAIAudioToTextService> factory = (serviceProvider, _) =>
            new(deploymentName, openAIClient ?? serviceProvider.GetRequiredService<AzureOpenAIClient>(), modelId, serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IAudioToTextService>(serviceId, factory);

        return builder;
    }

    #endregion

    private static AzureOpenAIClient CreateAzureOpenAIClient(string endpoint, ApiKeyCredential credentials, HttpClient? httpClient, string? apiVersion) =>
        new(new Uri(endpoint), credentials, AzureClientCore.GetAzureOpenAIClientOptions(httpClient, apiVersion));

    private static AzureOpenAIClient CreateAzureOpenAIClient(string endpoint, TokenCredential credentials, HttpClient? httpClient, string? apiVersion) =>
        new(new Uri(endpoint), credentials, AzureClientCore.GetAzureOpenAIClientOptions(httpClient, apiVersion));
}
