// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Azure.Core;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure OpenAI and AzureOpenAI connectors.
/// </summary>
public static class AzureOpenAIMemoryBuilderExtensions
{
    /// <summary>
    /// Adds an Azure OpenAI text embeddings service.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="modelId">Model identifier</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>Self instance</returns>
    [Experimental("SKEXP0010")]
    public static MemoryBuilder WithAzureOpenAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        string? modelId = null,
        HttpClient? httpClient = null,
        int? dimensions = null)
    {
        return builder.WithTextEmbeddingGeneration((loggerFactory, builderHttpClient) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                apiKey,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient ?? builderHttpClient),
                loggerFactory,
                dimensions));
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
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <returns>Self instance</returns>
    [Experimental("SKEXP0010")]
    public static MemoryBuilder WithAzureOpenAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? modelId = null,
        HttpClient? httpClient = null,
        int? dimensions = null)
    {
        return builder.WithTextEmbeddingGeneration((loggerFactory, builderHttpClient) =>
            new AzureOpenAITextEmbeddingGenerationService(
                deploymentName,
                endpoint,
                credential,
                modelId,
                HttpClientProvider.GetHttpClient(httpClient ?? builderHttpClient),
                loggerFactory,
                dimensions));
    }
}
