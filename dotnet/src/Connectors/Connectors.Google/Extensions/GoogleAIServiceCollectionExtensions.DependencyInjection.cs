// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extensions for adding GoogleAI generation services to the application.
/// </summary>
public static class GoogleAIServiceCollectionExtensions
{
    /// <summary>
    /// Add Google AI <see cref="IEmbeddingGenerator{String, Embedding}"/> to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Embeddings Generation service to.</param>
    /// <param name="modelId">The model for embeddings generation.</param>
    /// <param name="apiKey">The API key for authentication Gemini API.</param>
    /// <param name="apiVersion">The version of the Google API.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <param name="dimensions">The optional number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddGoogleAIEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        GoogleAIVersion apiVersion = GoogleAIVersion.V1_Beta, // todo: change beta to stable when stable version will be available
        string? serviceId = null,
        HttpClient? httpClient = null,
        int? dimensions = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);

        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
            new GoogleAIEmbeddingGenerator(
                modelId: modelId,
                apiKey: apiKey,
                apiVersion: apiVersion,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>(),
                dimensions: dimensions));
    }

#if NET
    /// <summary>
    /// Add Google AI <see cref="IChatClient"/> to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Google AI Chat Client to.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="apiKey">The API key for authentication with the Google AI API.</param>
    /// <param name="vertexAI">Whether to use Vertex AI.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddGoogleAIChatClient(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        bool vertexAI = false,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var googleClient = new Google.GenAI.Client(apiKey: apiKey, vertexAI: vertexAI);

            var builder = new GoogleGenAIChatClient(googleClient, modelId)
                .AsBuilder()
                .UseKernelFunctionInvocation(loggerFactory)
                .UseOpenTelemetry(loggerFactory, openTelemetrySourceName, openTelemetryConfig);

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder.Build();
        }

        services.AddKeyedSingleton<IChatClient>(serviceId, (Func<IServiceProvider, object?, IChatClient>)Factory);

        return services;
    }

    /// <summary>
    /// Add Google AI <see cref="IChatClient"/> to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Google AI Chat Client to.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="googleClient">The <see cref="Google.GenAI.Client"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddGoogleAIChatClient(
        this IServiceCollection services,
        string modelId,
        Google.GenAI.Client? googleClient = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var client = googleClient ?? serviceProvider.GetRequiredService<Google.GenAI.Client>();

            var builder = new GoogleGenAIChatClient(client, modelId)
                .AsBuilder()
                .UseKernelFunctionInvocation(loggerFactory)
                .UseOpenTelemetry(loggerFactory, openTelemetrySourceName, openTelemetryConfig);

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder.Build();
        }

        services.AddKeyedSingleton<IChatClient>(serviceId, (Func<IServiceProvider, object?, IChatClient>)Factory);

        return services;
    }
#endif
}
