// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Azure.AI.Inference;
using Azure.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureAIInference.Core;
using AzureKeyCredential = Azure.AzureKeyCredential;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Provides extension methods for <see cref="IServiceCollection"/> to configure Azure AI Inference connectors.
/// </summary>
public static class AzureAIInferenceServiceCollectionExtensions
{
    #region EmbeddingGenerator
    /// <summary>
    /// Add an Azure AI Inference <see cref="IEmbeddingGenerator"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    public static IServiceCollection AddAzureAIInferenceEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        string? apiKey = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryEmbeddingGenerator<string, Embedding<float>>>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
        {
            httpClient ??= serviceProvider.GetService<HttpClient>();
            var options = ChatClientCore.GetClientOptions(httpClient);
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = new EmbeddingsClient(endpoint, new AzureKeyCredential(apiKey ?? SingleSpace), options)
                .AsIEmbeddingGenerator(modelId).AsBuilder();

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory).Build();
            }

            builder.UseOpenTelemetry(loggerFactory, openTelemetrySourceName, openTelemetryConfig);

            return builder.Build();
        });
    }

    /// <summary>
    /// Add an Azure AI Inference <see cref="IEmbeddingGenerator"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    public static IServiceCollection AddAzureAIInferenceEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        TokenCredential credential,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryEmbeddingGenerator<string, Embedding<float>>>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
        {
            httpClient ??= serviceProvider.GetService<HttpClient>();
            var options = ChatClientCore.GetClientOptions(httpClient);

            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();
            var builder = new EmbeddingsClient(endpoint, credential, options)
                .AsIEmbeddingGenerator(modelId)
                .AsBuilder();

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory).Build();
            }

            builder.UseOpenTelemetry(loggerFactory, openTelemetrySourceName, openTelemetryConfig);

            return builder.Build();
        });
    }
    #endregion

    #region ChatClient
    /// <summary>
    /// Adds an Azure AI Inference <see cref="IChatClient"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Target Model Id</param>
    /// <param name="apiKey">API Key</param>
    /// <param name="endpoint">Endpoint / Target URI</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="openTelemetrySourceName">An optional source name that will be used on the telemetry data.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureAIInferenceChatClient(
        this IServiceCollection services,
        string modelId,
        string? apiKey = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        return services.AddKeyedSingleton<IChatClient>(serviceId, (serviceProvider, _) =>
        {
            httpClient ??= serviceProvider.GetService<HttpClient>();
            var options = ChatClientCore.GetClientOptions(httpClient);

            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = new ChatCompletionsClient(endpoint, new AzureKeyCredential(apiKey ?? SingleSpace), options)
                .AsIChatClient(modelId)
                .AsBuilder();

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder
                    .UseKernelFunctionInvocation(loggerFactory)
                    .UseOpenTelemetry(loggerFactory, openTelemetrySourceName, openTelemetryConfig)
                    .Build(serviceProvider);
        });
    }

    /// <summary>
    /// Adds an Azure AI Inference <see cref="IChatClient"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Target Model Id</param>
    /// <param name="credential">Token credential, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="endpoint">Endpoint / Target URI</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="openTelemetrySourceName">An optional source name that will be used on the telemetry data.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureAIInferenceChatClient(
        this IServiceCollection services,
        string modelId,
        TokenCredential credential,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        return services.AddKeyedSingleton<IChatClient>(serviceId, (serviceProvider, _) =>
        {
            httpClient ??= serviceProvider.GetService<HttpClient>();
            var options = ChatClientCore.GetClientOptions(httpClient);

            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = new ChatCompletionsClient(endpoint, credential, options)
                .AsIChatClient(modelId)
                .AsBuilder();

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder
                    .UseKernelFunctionInvocation(loggerFactory)
                    .UseOpenTelemetry(loggerFactory, openTelemetrySourceName, openTelemetryConfig)
                    .Build(serviceProvider);
        });
    }

    /// <summary>
    /// Adds an Azure AI Inference <see cref="IChatClient"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Azure AI Inference model id</param>
    /// <param name="chatClient"><see cref="ChatCompletionsClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="openTelemetrySourceName">An optional source name that will be used on the telemetry data.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddAzureAIInferenceChatClient(this IServiceCollection services,
        string modelId,
        ChatCompletionsClient? chatClient = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        return services.AddKeyedSingleton<IChatClient>(serviceId, (serviceProvider, _) =>
        {
            chatClient ??= serviceProvider.GetRequiredService<ChatCompletionsClient>();

            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = chatClient
                .AsIChatClient(modelId)
                .AsBuilder();

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder
                .UseKernelFunctionInvocation(loggerFactory)
                .UseOpenTelemetry(loggerFactory, openTelemetrySourceName, openTelemetryConfig)
                .Build(serviceProvider);
        });
    }
    #endregion ChatClient

    #region Private
    /// <summary>
    /// When using Azure AI Inference against Gateway APIs that don't require an API key,
    /// this single space is used to avoid breaking the client.
    /// </summary>
    private const string SingleSpace = " ";
    #endregion
}
