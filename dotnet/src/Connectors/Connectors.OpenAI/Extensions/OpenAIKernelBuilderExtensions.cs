// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
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
using OpenAI;

#pragma warning disable IDE0039 // Use local function

namespace Microsoft.SemanticKernel;

/// <summary>
/// Sponsor extensions class for <see cref="IKernelBuilder"/>.
/// </summary>
public static class OpenAIKernelBuilderExtensions
{
    #region Text Embedding
    /// <summary>
    /// Adds <see cref="OpenAITextEmbeddingGenerationService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
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
    /// Adds the <see cref="OpenAITextEmbeddingGenerationService"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
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
    #endregion

    #region Text to Image
    /// <summary>
    /// Add the OpenAI Dall-E text to image service to the list
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="modelId">The model to use for image generation.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAITextToImage(
        this IKernelBuilder builder,
        string apiKey,
        string? orgId = null,
        string? modelId = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddKeyedSingleton<ITextToImageService>(serviceId, (serviceProvider, _) =>
            new OpenAITextToImageService(
                apiKey,
                orgId,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }
    #endregion

    #region Text to Audio

    /// <summary>
    /// Adds the OpenAI text-to-audio service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
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
    #endregion

    #region Audio-to-Text

    /// <summary>
    /// Adds the OpenAI audio-to-text service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
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
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model id</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
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

    #endregion

    #region Files

    /// <summary>
    /// Adds the <see cref="OpenAIFileService"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    [Obsolete("Use OpenAI SDK or AzureOpenAI SDK clients for file operations.")]
    [ExcludeFromCodeCoverage]
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

    #endregion

    #region Chat Completion

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
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

        OpenAIChatCompletionService Factory(IServiceProvider serviceProvider, object? _) =>
            new(modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (Func<IServiceProvider, object?, OpenAIChatCompletionService>)Factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (Func<IServiceProvider, object?, OpenAIChatCompletionService>)Factory);

        return builder;
    }

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model id</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddOpenAIChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);

        OpenAIChatCompletionService Factory(IServiceProvider serviceProvider, object? _) =>
            new(modelId, openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>(), serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (Func<IServiceProvider, object?, OpenAIChatCompletionService>)Factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (Func<IServiceProvider, object?, OpenAIChatCompletionService>)Factory);

        return builder;
    }

    /// <summary>
    /// Adds the Custom Endpoint OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="endpoint">Custom OpenAI Compatible Message API endpoint</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
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

        OpenAIChatCompletionService Factory(IServiceProvider serviceProvider, object? _) =>
            new(modelId: modelId,
                apiKey: apiKey,
                endpoint: endpoint,
                organization: orgId,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>());

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (Func<IServiceProvider, object?, OpenAIChatCompletionService>)Factory);
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (Func<IServiceProvider, object?, OpenAIChatCompletionService>)Factory);

        return builder;
    }

    #endregion
}
