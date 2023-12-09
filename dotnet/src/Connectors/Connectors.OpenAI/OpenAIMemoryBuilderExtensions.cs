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
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    [Experimental("SKEXP0011")]
    public static MemoryBuilder WithAzureOpenAITextEmbeddingGeneration(
        this MemoryBuilder builder,
        string deploymentName,
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null) => WithAzureOpenAITextEmbeddingGeneration(builder, new() { DeploymentName = deploymentName, Endpoint = endpoint, ApiKey = apiKey }, httpClient);

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
        HttpClient? httpClient = null) => WithOpenAITextEmbeddingGeneration(builder, new() { ModelId = modelId, ApiKey = apiKey, Organization = orgId }, httpClient);

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
