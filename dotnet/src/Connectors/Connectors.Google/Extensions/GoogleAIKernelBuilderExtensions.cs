// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding GoogleAI generation services to the application.
/// </summary>
public static class GoogleAIKernelBuilderExtensions
{
    /// <summary>
    /// Add Google AI Gemini Chat Completion and Text Generation services to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="apiKey">The API key for authentication Gemini API.</param>
    /// <param name="apiVersion">The version of the Google API.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddGoogleAIGeminiChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        GoogleAIVersion apiVersion = GoogleAIVersion.V1_Beta, // todo: change beta to stable when stable version will be available
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new GoogleAIGeminiChatCompletionService(
                modelId: modelId,
                apiKey: apiKey,
                apiVersion: apiVersion,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return builder;
    }

    /// <summary>
    /// Add Google AI <see cref="ITextEmbeddingGenerationService"/> to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="apiKey">The API key for authentication Gemini API.</param>
    /// <param name="apiVersion">The version of the Google API.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <param name="dimensions">The optional number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    /// <returns>The updated kernel builder.</returns>
    [Obsolete("Use AddGoogleAIEmbeddingGenerator instead.")]
    public static IKernelBuilder AddGoogleAIEmbeddingGeneration(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        GoogleAIVersion apiVersion = GoogleAIVersion.V1_Beta, // todo: change beta to stable when stable version will be available
        string? serviceId = null,
        HttpClient? httpClient = null,
        int? dimensions = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);

        builder.Services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new GoogleAITextEmbeddingGenerationService(
                modelId: modelId,
                apiKey: apiKey,
                apiVersion: apiVersion,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>(),
                dimensions: dimensions));
        return builder;
    }

    /// <summary>
    /// Add Google AI <see cref="IEmbeddingGenerator{String, Embedding}"/> to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="apiKey">The API key for authentication Gemini API.</param>
    /// <param name="apiVersion">The version of the Google API.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <param name="dimensions">The optional number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddGoogleAIEmbeddingGenerator(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        GoogleAIVersion apiVersion = GoogleAIVersion.V1_Beta, // todo: change beta to stable when stable version will be available
        string? serviceId = null,
        HttpClient? httpClient = null,
        int? dimensions = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);

        builder.Services.AddGoogleAIEmbeddingGenerator(
            modelId: modelId,
            apiKey: apiKey,
            apiVersion: apiVersion,
            serviceId: serviceId,
            httpClient: httpClient,
            dimensions: dimensions);
        return builder;
    }

#if NET
    /// <summary>
    /// Add Google AI <see cref="IChatClient"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="apiKey">The API key for authentication with the Google AI API.</param>
    /// <param name="vertexAI">Whether to use Vertex AI.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddGoogleAIChatClient(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        bool vertexAI = false,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddGoogleAIChatClient(
            modelId,
            apiKey,
            vertexAI,
            serviceId,
            openTelemetrySourceName,
            openTelemetryConfig);

        return builder;
    }

    /// <summary>
    /// Add Google AI <see cref="IChatClient"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="googleClient">The <see cref="Google.GenAI.Client"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddGoogleAIChatClient(
        this IKernelBuilder builder,
        string modelId,
        Google.GenAI.Client? googleClient = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddGoogleAIChatClient(
            modelId,
            googleClient,
            serviceId,
            openTelemetrySourceName,
            openTelemetryConfig);

        return builder;
    }
#endif
}
