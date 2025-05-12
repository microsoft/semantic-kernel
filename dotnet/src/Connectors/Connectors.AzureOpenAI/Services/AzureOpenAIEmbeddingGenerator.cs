// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Azure OpenAI text embedding service.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class AzureOpenAIEmbeddingGenerator : IEmbeddingGenerator<string, Embedding<float>>
{
    private readonly AzureClientCore _client;
    private readonly AzureOpenAIEmbeddingGeneratorMetadata _metadata;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIEmbeddingGenerator"/> class.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAIEmbeddingGenerator(
        string deploymentName,
        string endpoint,
        string apiKey,
        string? modelId = null,
        int? dimensions = null,
        string? apiVersion = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new(deploymentName, endpoint, apiKey, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAIEmbeddingGenerator)), apiVersion);
        this._client.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);

        this._metadata = new(deploymentName: deploymentName, providerName: "Azure OpenAI", defaultModelId: modelId ?? deploymentName, providerUri: this._client.Endpoint, defaultModelDimensions: dimensions, apiVersion: apiVersion);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIEmbeddingGenerator"/> class.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAIEmbeddingGenerator(
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? modelId = null,
        int? dimensions = null,
        string? apiVersion = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new(deploymentName, endpoint, credential, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAIEmbeddingGenerator)), apiVersion);

        this._client.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);

        this._metadata = new(deploymentName: deploymentName, providerName: "Azure OpenAI", defaultModelId: modelId ?? deploymentName, providerUri: this._client.Endpoint, defaultModelDimensions: dimensions, apiVersion: apiVersion);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="azureOpenAIClient">Custom <see cref="AzureOpenAIClient"/> for HTTP requests.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAIEmbeddingGenerator(
        string deploymentName,
        AzureOpenAIClient azureOpenAIClient,
        string? modelId = null,
        int? dimensions = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new(deploymentName, azureOpenAIClient, loggerFactory?.CreateLogger(typeof(AzureOpenAIEmbeddingGenerator)));

        this._client.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);

        this._metadata = new(deploymentName: deploymentName, providerName: "Azure OpenAI", defaultModelId: modelId ?? deploymentName, providerUri: this._client.Endpoint, defaultModelDimensions: dimensions);
    }

    /// <inheritdoc />
    public async Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(IEnumerable<string> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
    {
        var result = await this._client.GetEmbeddingsAsync(this._client.DeploymentName, values.ToList(), kernel: null, options?.Dimensions ?? this._metadata.DefaultModelDimensions, cancellationToken).ConfigureAwait(false);
        return new(result.Select(e => new Embedding<float>(e)));
    }

    /// <inheritdoc />
    public void Dispose()
    {
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(EmbeddingGeneratorMetadata) ? this._metadata :
            serviceType == typeof(AzureOpenAIEmbeddingGeneratorMetadata) ? this._metadata :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
