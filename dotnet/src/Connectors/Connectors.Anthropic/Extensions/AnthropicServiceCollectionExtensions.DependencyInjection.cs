// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using Anthropic;
using Anthropic.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods for registering Anthropic services in <see cref="IServiceCollection"/>.
/// </summary>
[Experimental("SKEXP0001")]
public static class AnthropicServiceCollectionExtensions
{
    #region IChatClient Extensions (M.E.AI)

    /// <summary>
    /// Adds the Anthropic chat client to the service collection.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Anthropic model name (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="apiKey">Anthropic API key.</param>
    /// <param name="baseUrl">Base URL for the API endpoint. Defaults to https://api.anthropic.com.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">
    /// The HttpClient to use with this service.
    /// If not provided, one is resolved from the service provider or created with default 100-second timeout.
    /// </param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    /// <remarks>
    /// <para>
    /// <b>Retry and Timeout Policy:</b> This method follows the Semantic Kernel pattern of delegating
    /// retry and timeout handling to the <see cref="HttpClient"/> layer rather than the SDK layer.
    /// This prevents conflicting retry/timeout behavior when both layers attempt to handle failures.
    /// </para>
    /// <para>
    /// Configure your <see cref="HttpClient"/> (via <c>IHttpClientFactory</c>) with appropriate timeout and retry policies.
    /// </para>
    /// </remarks>
    public static IServiceCollection AddAnthropicChatClient(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        Uri? baseUrl = null,
        string? serviceId = null,
        HttpClient? httpClient = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            // Retry and timeout are intentionally disabled at SDK level.
            // The HttpClient layer handles these concerns (see method remarks).
            // - Default HttpClient has 100-second timeout
            // - Use IHttpClientFactory + Polly for retry policies
            var clientOptions = new ClientOptions
            {
                APIKey = apiKey,
                MaxRetries = 0,                      // Disabled: HttpClient/Polly handles retries
                Timeout = Timeout.InfiniteTimeSpan   // Disabled: HttpClient.Timeout applies
            };

            if (baseUrl is not null)
            {
                clientOptions.BaseUrl = baseUrl;
            }

            clientOptions.HttpClient = HttpClientProvider.GetHttpClient(httpClient, serviceProvider);

            var anthropicClient = new AnthropicClient(clientOptions);

            // Use shared pipeline helper for consistent behavior across Service and DI
            return AnthropicPipelineHelpers.BuildChatClientPipeline(
                anthropicClient,
                modelId,
                loggerFactory,
                openTelemetrySourceName,
                openTelemetryConfig);
        }

        services.AddKeyedSingleton<IChatClient>(serviceId, (Func<IServiceProvider, object?, IChatClient>)Factory);

        return services;
    }

    /// <summary>
    /// Adds the Anthropic chat client to the service collection using an existing AnthropicClient.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Anthropic model name (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="anthropicClient"><see cref="AnthropicClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    /// <remarks>
    /// Retry and timeout policies are determined by the <see cref="AnthropicClient"/> configuration and its
    /// underlying <see cref="HttpClient"/>. Anthropic-specific options are supplied via
    /// <see cref="AnthropicPromptExecutionSettings"/> when invoking chat or text operations.
    /// </remarks>
    public static IServiceCollection AddAnthropicChatClient(
        this IServiceCollection services,
        string modelId,
        AnthropicClient? anthropicClient = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();
            var client = anthropicClient ?? serviceProvider.GetRequiredService<AnthropicClient>();

            // Use shared pipeline helper for consistent behavior across Service and DI
            return AnthropicPipelineHelpers.BuildChatClientPipeline(
                client,
                modelId,
                loggerFactory,
                openTelemetrySourceName,
                openTelemetryConfig);
        }

        services.AddKeyedSingleton<IChatClient>(serviceId, (Func<IServiceProvider, object?, IChatClient>)Factory);

        return services;
    }

    #endregion

    #region IChatCompletionService Extensions (SK Legacy)

    /// <summary>
    /// Adds Anthropic chat completion service to the service collection.
    /// </summary>
    /// <param name="services">The service collection to add the service to.</param>
    /// <param name="modelId">The Anthropic model ID (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="apiKey">The API key for authentication.</param>
    /// <param name="baseUrl">The base URL for the API endpoint. Defaults to https://api.anthropic.com.</param>
    /// <param name="serviceId">Optional service identifier for keyed registration.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The service collection for chaining.</returns>
    public static IServiceCollection AddAnthropicChatCompletion(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        Uri? baseUrl = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        // Register the concrete service as a keyed singleton, then alias the interfaces to it.
        // This ensures a single instance is shared across IChatCompletionService and ITextGenerationService.
        services.AddKeyedSingleton<AnthropicChatCompletionService>(serviceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                modelId,
                apiKey,
                baseUrl,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));

        services.AddKeyedSingleton<IChatCompletionService>(serviceId,
            (serviceProvider, key) => serviceProvider.GetRequiredKeyedService<AnthropicChatCompletionService>(key));
        services.AddKeyedSingleton<ITextGenerationService>(serviceId,
            (serviceProvider, key) => serviceProvider.GetRequiredKeyedService<AnthropicChatCompletionService>(key));

        return services;
    }

    /// <summary>
    /// Adds Anthropic chat completion service to the service collection using an existing AnthropicClient.
    /// </summary>
    /// <param name="services">The service collection to add the service to.</param>
    /// <param name="modelId">The Anthropic model ID (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="anthropicClient">Pre-configured <see cref="AnthropicClient"/>. If null, will be resolved from the service provider.</param>
    /// <param name="serviceId">Optional service identifier for keyed registration.</param>
    /// <returns>The service collection for chaining.</returns>
    public static IServiceCollection AddAnthropicChatCompletion(
        this IServiceCollection services,
        string modelId,
        AnthropicClient? anthropicClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);

        // Register the concrete service as a keyed singleton, then alias the interfaces to it.
        // This ensures a single instance is shared across IChatCompletionService and ITextGenerationService.
        services.AddKeyedSingleton<AnthropicChatCompletionService>(serviceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                modelId,
                anthropicClient ?? serviceProvider.GetRequiredService<AnthropicClient>(),
                serviceProvider.GetService<ILoggerFactory>()));

        services.AddKeyedSingleton<IChatCompletionService>(serviceId,
            (serviceProvider, key) => serviceProvider.GetRequiredKeyedService<AnthropicChatCompletionService>(key));
        services.AddKeyedSingleton<ITextGenerationService>(serviceId,
            (serviceProvider, key) => serviceProvider.GetRequiredKeyedService<AnthropicChatCompletionService>(key));

        return services;
    }

    #endregion
}
