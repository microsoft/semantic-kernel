// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;

/// <summary>
/// Azure OpenAI text embedding service.
/// </summary>
public sealed class AzureOpenAITextEmbeddingGeneration : AzureOpenAIClientBase, ITextEmbeddingGeneration
{
    /// <summary>
    /// Creates a new <see cref="AzureOpenAITextEmbeddingGeneration"/> client instance using API Key auth.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextEmbeddingGeneration(
        string deploymentName,
        string endpoint,
        string apiKey,
        string? modelId = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null) : base(deploymentName, endpoint, apiKey, httpClient, loggerFactory)
    {
        this.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <summary>
    /// Creates a new <see cref="AzureOpenAITextEmbeddingGeneration"/> client instance supporting AAD auth.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextEmbeddingGeneration(
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        string? modelId = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null) : base(deploymentName, endpoint, credential, httpClient, loggerFactory)
    {
        this.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <summary>
    /// Creates a new <see cref="AzureOpenAITextEmbeddingGeneration"/> client.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="modelId">Azure OpenAI model id, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextEmbeddingGeneration(
        string deploymentName,
        OpenAIClient openAIClient,
        string? modelId = null,
        ILoggerFactory? loggerFactory = null) : base(deploymentName, openAIClient, loggerFactory)
    {
        this.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this.InternalAttributes;

    /// <inheritdoc/>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this.LogActionDetails();
        return this.InternalGetEmbeddingsAsync(data, kernel, cancellationToken);
    }
}
