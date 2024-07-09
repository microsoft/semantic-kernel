// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
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
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="apiKey">The API key for authentication Anthropic API.</param>
    /// <param name="options">Optional options for the anthropic client</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddAnthropicChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        ClientOptions? options = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(modelId);
        Verify.NotNull(apiKey);

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                modelId: modelId,
                apiKey: apiKey,
                options: options,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return builder;
    }

    /// <summary>
    /// Add Anthropic Chat Completion and Text Generation services to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="endpoint">Endpoint for the chat completion model</param>
    /// <param name="options">Options for the anthropic client</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddAnthropicChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        Uri endpoint,
        ClientOptions options,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(modelId);
        Verify.NotNull(endpoint);
        Verify.NotNull(options);

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new AnthropicChatCompletionService(
                modelId: modelId,
                endpoint: endpoint,
                options: options,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return builder;
    }
}
