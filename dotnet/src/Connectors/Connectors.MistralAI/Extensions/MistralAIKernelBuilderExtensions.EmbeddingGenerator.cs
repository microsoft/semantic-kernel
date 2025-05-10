// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for adding MistralAI embedding generator to a kernel builder.
/// </summary>
public static partial class MistralAIKernelBuilderExtensions
{
    /// <summary>
    /// Adds a MistralAI embedding generator service to the kernel.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">The name of the MistralAI modelId.</param>
    /// <param name="apiKey">The API key required for accessing the MistralAI service.</param>
    /// <param name="endpoint">Optional uri endpoint including the port where MistralAI server is hosted. Default is https://api.mistral.ai.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have, if supported by the model.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddMistralEmbeddingGenerator(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        Uri? endpoint = null,
        string? serviceId = null,
        int? dimensions = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddMistralEmbeddingGenerator(
            modelId,
            apiKey,
            endpoint,
            serviceId,
            dimensions,
            httpClient);

        return builder;
    }
}
