// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Sponsor extensions class for <see cref="IKernelBuilder"/>.
/// </summary>
public static partial class OpenAIKernelBuilderExtensions
{
    /// <summary>
    /// Adds <see cref="OpenAIEmbeddingGenerator"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAIEmbeddingGenerator(
        this IKernelBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        int? dimensions = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        builder.Services.AddOpenAIEmbeddingGenerator(
            modelId,
            apiKey,
            orgId,
            dimensions,
            serviceId,
            httpClient);

        return builder;
    }

    /// <summary>
    /// Adds the <see cref="OpenAIEmbeddingGenerator"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="openAIClient"><see cref="OpenAIClient"/> to use for the service. If null, one must be available in the service provider when this service is resolved.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Experimental("SKEXP0010")]
    public static IKernelBuilder AddOpenAIEmbeddingGenerator(
        this IKernelBuilder builder,
        string modelId,
        OpenAIClient? openAIClient = null,
        int? dimensions = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);
        Verify.NotNullOrWhiteSpace(modelId);

        builder.Services.AddOpenAIEmbeddingGenerator(
            modelId,
            openAIClient,
            dimensions,
            serviceId);

        return builder;
    }
}
