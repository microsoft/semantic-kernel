// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Anthropic;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.Anthropic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="IKernelBuilder"/>.
/// </summary>
[Experimental("SKEXP0001")]
public static class AnthropicKernelBuilderExtensions
{
    /// <summary>
    /// Adds Anthropic chat completion service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder to add the service to.</param>
    /// <param name="modelId">The Anthropic model ID (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="apiKey">The API key for authentication.</param>
    /// <param name="baseUrl">The base URL for the API endpoint. Defaults to https://api.anthropic.com.</param>
    /// <param name="serviceId">Optional service identifier for keyed registration.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The kernel builder for chaining.</returns>
    /// <remarks>
    /// Anthropic-specific options are configured via <see cref="AnthropicPromptExecutionSettings"/>.
    /// </remarks>
    public static IKernelBuilder AddAnthropicChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        Uri? baseUrl = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAnthropicChatCompletion(modelId, apiKey, baseUrl, serviceId, httpClient);
        return builder;
    }

    /// <summary>
    /// Adds Anthropic chat completion service to the kernel builder using an existing AnthropicClient.
    /// </summary>
    /// <param name="builder">The kernel builder to add the service to.</param>
    /// <param name="modelId">The Anthropic model ID (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="anthropicClient">Pre-configured <see cref="AnthropicClient"/>. If null, will be resolved from the service provider.</param>
    /// <param name="serviceId">Optional service identifier for keyed registration.</param>
    /// <returns>The kernel builder for chaining.</returns>
    /// <remarks>
    /// Anthropic-specific options are configured via <see cref="AnthropicPromptExecutionSettings"/>.
    /// </remarks>
    public static IKernelBuilder AddAnthropicChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        AnthropicClient? anthropicClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAnthropicChatCompletion(modelId, anthropicClient, serviceId);
        return builder;
    }

    /// <summary>
    /// Adds the Anthropic chat client to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder to add the service to.</param>
    /// <param name="modelId">Anthropic model name (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="apiKey">Anthropic API key.</param>
    /// <param name="baseUrl">Base URL for the API endpoint. Defaults to https://api.anthropic.com.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The kernel builder for chaining.</returns>
    /// <remarks>
    /// Anthropic-specific options are configured via <see cref="AnthropicPromptExecutionSettings"/>.
    /// </remarks>
    public static IKernelBuilder AddAnthropicChatClient(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        Uri? baseUrl = null,
        string? serviceId = null,
        HttpClient? httpClient = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAnthropicChatClient(modelId, apiKey, baseUrl, serviceId, httpClient, openTelemetrySourceName, openTelemetryConfig);
        return builder;
    }

    /// <summary>
    /// Adds the Anthropic chat client to the kernel builder using an existing AnthropicClient.
    /// </summary>
    /// <param name="builder">The kernel builder to add the service to.</param>
    /// <param name="modelId">Anthropic model name (e.g., claude-sonnet-4-20250514).</param>
    /// <param name="anthropicClient"><see cref="AnthropicClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="openTelemetrySourceName">An optional name for the OpenTelemetry source.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>The kernel builder for chaining.</returns>
    /// <remarks>
    /// Anthropic-specific options are configured via <see cref="AnthropicPromptExecutionSettings"/>.
    /// </remarks>
    public static IKernelBuilder AddAnthropicChatClient(
        this IKernelBuilder builder,
        string modelId,
        AnthropicClient? anthropicClient = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddAnthropicChatClient(modelId, anthropicClient, serviceId, openTelemetrySourceName, openTelemetryConfig);
        return builder;
    }
}
