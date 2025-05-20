// Copyright (c) Microsoft. All rights reserved.

using System;
using Amazon.BedrockRuntime;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding Bedrock modality services to the <see cref="IKernelBuilder" /> configuration.
/// </summary>
public static class BedrockKernelBuilderExtensions
{
    /// <summary>
    /// Add Amazon Bedrock <see cref="IChatCompletionService"/> to the <see cref="IKernelBuilder" /> using <see cref="IAmazonBedrockRuntime"/> object.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>Returns back <see cref="IKernelBuilder"/> with a configured service.</returns>
    public static IKernelBuilder AddBedrockChatCompletionService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddBedrockChatCompletionService(modelId, bedrockRuntime, serviceId);

        return builder;
    }

    /// <summary>Add Amazon Bedrock <see cref="IChatClient"/> to the <see cref="IKernelBuilder" />.</summary>
    /// <param name="builder">The service collection.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="openTelemetrySourceName">An optional source name that will be used on the telemetry data.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryChatClient"/> instance.</param>
    /// <returns>Returns back <see cref="IKernelBuilder"/> with a configured <see cref="IChatClient"/>.</returns>
    public static IKernelBuilder AddBedrockChatClient(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddBedrockChatClient(modelId, bedrockRuntime, serviceId, openTelemetrySourceName, openTelemetryConfig);

        return builder;
    }

    /// <summary>
    /// Add Amazon Bedrock Text Generation service to the <see cref="IKernelBuilder" /> using <see cref="IAmazonBedrockRuntime"/> object.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>Returns back <see cref="IKernelBuilder"/> with a configured service.</returns>
    public static IKernelBuilder AddBedrockTextGenerationService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddBedrockTextGenerationService(modelId, bedrockRuntime, serviceId);

        return builder;
    }

    /// <summary>
    /// Add Amazon Bedrock Text Generation service to the <see cref="IKernelBuilder" /> using <see cref="IAmazonBedrockRuntime"/> object.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for embedding generation.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>Returns back <see cref="IKernelBuilder"/> with a configured service.</returns>
    [Obsolete("Use AddBedrockEmbeddingGenerator instead.")]
    public static IKernelBuilder AddBedrockTextEmbeddingGenerationService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddBedrockTextEmbeddingGenerationService(modelId, bedrockRuntime, serviceId);

        return builder;
    }

    /// <summary>
    /// Add Amazon Bedrock <see cref="IEmbeddingGenerator"/> to the <see cref="IKernelBuilder" /> using <see cref="IAmazonBedrockRuntime"/> object.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for embedding generation.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="openTelemetrySourceName">An optional source name that will be used on the telemetry data.</param>
    /// <param name="openTelemetryConfig">An optional callback that can be used to configure the <see cref="OpenTelemetryEmbeddingGenerator{String, Embedding}"/> instance.</param>
    /// <returns>Returns back <see cref="IKernelBuilder"/> with a configured <see cref="IEmbeddingGenerator"/>.</returns>
    public static IKernelBuilder AddBedrockEmbeddingGenerator(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryEmbeddingGenerator<string, Embedding<float>>>? openTelemetryConfig = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddBedrockEmbeddingGenerator(modelId, bedrockRuntime, serviceId, openTelemetrySourceName, openTelemetryConfig);

        return builder;
    }
}
