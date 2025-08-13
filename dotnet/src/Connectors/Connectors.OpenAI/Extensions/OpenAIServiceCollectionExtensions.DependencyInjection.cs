// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Http;
using OpenAI;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Sponsor extensions class for <see cref="IServiceCollection"/>.
/// </summary>
public static class OpenAIServiceCollectionExtensions
{
    #region Chat Client

    /// <summary>
    /// White space constant.
    /// </summary>
    private const string SingleSpace = " ";

    /// <summary>
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAIChatClient(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            ClientCore.GetOpenAIClientOptions(
                endpoint: null,
                orgId: orgId,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider));

            var builder = new OpenAIClient(
                    credential: new ApiKeyCredential(apiKey ?? SingleSpace),
                    options: ClientCore.GetOpenAIClientOptions(HttpClientProvider.GetHttpClient(httpClient, serviceProvider)))
                .GetChatClient(modelId)
                .AsIChatClient()
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
    /// Adds the OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model id</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAIChatClient(this IServiceCollection services,
        string modelId,
        OpenAIClient? openAIClient = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = (openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>())
                .GetChatClient(modelId)
                .AsIChatClient()
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
    /// Adds the Custom OpenAI chat completion service to the list.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="endpoint">A Custom Message API compatible endpoint.</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOpenAIChatClient(
        this IServiceCollection services,
        string modelId,
        Uri endpoint,
        string? apiKey = null,
        string? orgId = null,
        string? serviceId = null,
        HttpClient? httpClient = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = new OpenAIClient(
                    credential: new ApiKeyCredential(apiKey ?? SingleSpace),
                    options: ClientCore.GetOpenAIClientOptions(
                        httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                        endpoint: endpoint,
                        orgId: orgId))
                .GetChatClient(modelId)
                .AsIChatClient()
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
    #endregion

    #region Embedding Generator
    /// <summary>
    /// Adds the <see cref="IEmbeddingGenerator{TInput, TEmbedding}"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="IEmbeddingGenerator{String, Embedding}"/> instance.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAIEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? orgId = null,
        int? dimensions = null,
        string? serviceId = null,
        HttpClient? httpClient = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryEmbeddingGenerator<string, Embedding<float>>>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = new OpenAIClient(
                   credential: new ApiKeyCredential(apiKey ?? SingleSpace),
                   options: ClientCore.GetOpenAIClientOptions(
                       httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                       orgId: orgId))
               .GetEmbeddingClient(modelId)
               .AsIEmbeddingGenerator(dimensions)
               .AsBuilder()
               .UseOpenTelemetry(loggerFactory, openTelemetrySourceName, openTelemetryConfig);

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder.Build();
        });
    }

    /// <summary>
    /// Adds the <see cref="IEmbeddingGenerator{TInput, TEmbedding}"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The OpenAI model id.</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="IEmbeddingGenerator{String, Embedding}"/> instance.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOpenAIEmbeddingGenerator(this IServiceCollection services,
        string modelId,
        OpenAIClient? openAIClient = null,
        int? dimensions = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryEmbeddingGenerator<string, Embedding<float>>>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = (openAIClient ?? serviceProvider.GetRequiredService<OpenAIClient>())
                .GetEmbeddingClient(modelId)
                .AsIEmbeddingGenerator(dimensions)
                .AsBuilder()
                .UseOpenTelemetry(loggerFactory, openTelemetrySourceName, openTelemetryConfig);

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder.Build();
        });
    }
    #endregion
}
