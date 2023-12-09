// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Azure.Core;
using Microsoft.SemanticKernel.Plugins.Memory;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure OpenAI and AzureOpenAI connectors.
/// </summary>
public static class OpenAIMemoryBuilderExtensions
{
    /// <summary>
    /// Adds an Azure OpenAI text embeddings service.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance</param>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    [Experimental("SKEXP0011")]
    public static MemoryBuilder WithAzureOpenAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        OpenAIServiceConfig serviceConfig,
        HttpClient? httpClient = null)
    {
        return builder.WithTextEmbeddingGeneration((loggerFactory, httpClient) =>
            new AzureOpenAITextEmbeddingGeneration(
                serviceConfig,
                HttpClientProvider.GetHttpClient(httpClient),
                loggerFactory));
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance</param>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    [Experimental("SKEXP0011")]
    public static MemoryBuilder WithAzureOpenAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        OpenAIServiceConfig serviceConfig,
        TokenCredential credential,
        HttpClient? httpClient = null)
    {
        return builder.WithTextEmbeddingGeneration((loggerFactory, httpClient) =>
            new AzureOpenAITextEmbeddingGeneration(
                serviceConfig,
                credential,
                HttpClientProvider.GetHttpClient(httpClient),
                loggerFactory));
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance</param>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    [Experimental("SKEXP0011")]
    public static MemoryBuilder WithOpenAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        OpenAIServiceConfig serviceConfig,
        HttpClient? httpClient = null)
    {
        return builder.WithTextEmbeddingGeneration((loggerFactory, httpClient) =>
            new OpenAITextEmbeddingGeneration(
                serviceConfig,
                HttpClientProvider.GetHttpClient(httpClient),
                loggerFactory));
    }
}
