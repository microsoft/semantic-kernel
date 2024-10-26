// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding Anthropic generation services to the application.
/// </summary>
public static class AnthropicKernelBuilderExtensions
{
    /// <summary>
    /// Add Anthropic Chat Completion and Text Generation services to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="apiKey">API key.</param>
    /// <param name="options">Optional options for the anthropic client</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <param name="serviceId">Service identifier.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddAnthropicChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        AnthropicClientOptions? options = null,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                modelId: modelId,
                apiKey: apiKey,
                options: options ?? new AnthropicClientOptions(),
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }

    /// <summary>
    /// Add Anthropic Chat Completion and Text Generation services to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">Model identifier.</param>
    /// <param name="bearerTokenProvider">Bearer token provider.</param>
    /// <param name="endpoint">Vertex AI Anthropic endpoint.</param>
    /// <param name="options">Optional options for the anthropic client</param>
    /// <param name="serviceId">Service identifier.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddAnthropicVertextAIChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        Uri? endpoint = null,
        VertexAIAnthropicClientOptions? options = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                modelId: modelId,
                bearerTokenProvider: bearerTokenProvider,
                options: options ?? new VertexAIAnthropicClientOptions(),
                endpoint: endpoint,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));

        return builder;
    }
}
