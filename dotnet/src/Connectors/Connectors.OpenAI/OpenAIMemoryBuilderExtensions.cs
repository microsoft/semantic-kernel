// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Azure.Core;
using Microsoft.SemanticKernel.Http;
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
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="modelId">Model identifier</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    [Experimental("SKEXP0011")]
    public static MemoryBuilder WithAzureOpenAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        string deploymentName,
        string modelId,
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null)
    {
        return builder.WithTextEmbeddingGeneration((loggerFactory, httpClient) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                modelId,
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(httpClient),
                loggerFactory));
    }

    /// <summary>
    /// Adds an Azure OpenAI text embeddings service.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Model identifier</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    [Experimental("SKEXP0011")]
    public static MemoryBuilder WithAzureOpenAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? modelId = null,
        HttpClient? httpClient = null)
    {
        return builder.WithTextEmbeddingGeneration((loggerFactory, httpClient) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                credential,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient),
                loggerFactory));
    }

    /// <summary>
    /// Adds the OpenAI text embeddings service.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    [Experimental("SKEXP0011")]
    public static MemoryBuilder WithOpenAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        string modelId,
        string apiKey,
        string? orgId = null,
        HttpClient? httpClient = null)
    {
        return builder.WithTextEmbeddingGeneration((loggerFactory, httpClient) =>
            new OpenAITextEmbeddingGenerationService(
                modelId,
                apiKey,
                orgId,
                HttpClientProvider.GetHttpClient(httpClient),
                loggerFactory));
    }
}
