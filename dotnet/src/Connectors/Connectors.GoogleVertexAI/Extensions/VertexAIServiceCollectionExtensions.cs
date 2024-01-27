// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding VertexAI generation services to the application.
/// </summary>
public static class VertexAIServiceCollectionExtensions
{
    /// <summary>
    /// Adds Vertex AI Gemini Text Generation service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="apiKey">The API key for authentication Gemini API.</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddVertexAIGeminiTextGeneration(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        string location,
        string projectId,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new VertexAIGeminiTextGenerationService(
                model: modelId,
                apiKey: apiKey,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return builder;
    }

    /// <summary>
    /// Adds Vertex AI Gemini Text Generation service to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="apiKey">The API key for authentication Gemini API.</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddVertexAIGeminiTextGeneration(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string location,
        string projectId,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new VertexAIGeminiTextGenerationService(
                model: modelId,
                apiKey: apiKey,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds Vertex AI Gemini Chat Completion and Text Generation services to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="apiKey">The API key for authentication Gemini API.</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddVertexAIGeminiChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        string location,
        string projectId,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new VertexAIGeminiChatCompletionService(
                model: modelId,
                apiKey: apiKey,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new VertexAIGeminiChatCompletionService(
                model: modelId,
                apiKey: apiKey,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return builder;
    }

    /// <summary>
    /// Adds Vertex AI Gemini Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="apiKey">The API key for authentication Gemini API.</param>
    /// <param name="location">The region to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddVertexAIGeminiChatCompletion(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string location,
        string projectId,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new VertexAIGeminiChatCompletionService(
                model: modelId,
                apiKey: apiKey,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new VertexAIGeminiChatCompletionService(
                model: modelId,
                apiKey: apiKey,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return services;
    }
}
