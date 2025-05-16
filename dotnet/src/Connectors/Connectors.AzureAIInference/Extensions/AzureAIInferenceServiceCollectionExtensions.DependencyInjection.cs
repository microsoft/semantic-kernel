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

    #region Private

    /// <summary>
    /// When using Azure AI Inference against Gateway APIs that don't require an API key,
    /// this single space is used to avoid breaking the client.
    /// </summary>
    private const string SingleSpace = " ";
    #endregion
}
