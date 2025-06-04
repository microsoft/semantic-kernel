// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Azure OpenAI text embedding service.
/// </summary>
[Experimental("SKEXP0010")]
[Obsolete("Use AddAzureOpenAIEmbeddingGenerator extension methods instead.")]
public sealed class AzureOpenAITextEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    private readonly AzureClientCore _client;
    private readonly int? _dimensions;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    public AzureOpenAITextEmbeddingGenerationService(
        string deploymentName,
        string endpoint,
        string apiKey,
        string? modelId = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        int? dimensions = null,
        string? apiVersion = null)
    {
        this._client = new(deploymentName, endpoint, apiKey, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAITextEmbeddingGenerationService)), apiVersion);

        this._client.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);

        this._dimensions = dimensions;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="apiVersion">Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/></param>
    public AzureOpenAITextEmbeddingGenerationService(
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? modelId = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null,
        int? dimensions = null,
        string? apiVersion = null)
    {
        this._client = new(deploymentName, endpoint, credential, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAITextEmbeddingGenerationService)), apiVersion);

        this._client.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);

        this._dimensions = dimensions;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAITextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="azureOpenAIClient">Custom <see cref="AzureOpenAIClient"/> for HTTP requests.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    public AzureOpenAITextEmbeddingGenerationService(
        string deploymentName,
        AzureOpenAIClient azureOpenAIClient,
        string? modelId = null,
        ILoggerFactory? loggerFactory = null,
        int? dimensions = null)
    {
        this._client = new(deploymentName, azureOpenAIClient, loggerFactory?.CreateLogger(typeof(AzureOpenAITextEmbeddingGenerationService)));

        this._client.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);

        this._dimensions = dimensions;
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._client.Attributes;

    /// <inheritdoc/>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this._client.GetEmbeddingsAsync(this._client.DeploymentName, data, kernel, this._dimensions, cancellationToken);
    }
}
