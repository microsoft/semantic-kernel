// Copyright (c) Microsoft. All rights reserved.

using System;
using Amazon.BedrockRuntime;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding Bedrock modality services to the kernel builder configuration.
/// </summary>
public static class BedrockKernelBuilderExtensions
{
    /// <summary>
    /// Add Amazon Bedrock Chat Completion service to the kernel builder using IAmazonBedrockRuntime object.
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

    /// <summary>
    /// Add Amazon Bedrock Text Generation service to the kernel builder using IAmazonBedrockRuntime object.
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
    /// Add Amazon Bedrock Text Generation service to the kernel builder using IAmazonBedrockRuntime object.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
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
    /// Add Amazon Bedrock Text Embedding Generation service to the kernel builder using IAmazonBedrockRuntime object.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text embedding generation.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have, if supported by the model.</param>
    /// <returns>Returns back <see cref="IKernelBuilder"/> with a configured service.</returns>
    public static IKernelBuilder AddBedrockEmbeddingGenerator(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null,
        int? dimensions = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddBedrockEmbeddingGenerator(modelId, bedrockRuntime, serviceId, dimensions);

        return builder;
    }
}
