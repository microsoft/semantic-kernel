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

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Azure OpenAI text embedding service.
/// </summary>
[Experimental("SKEXP0011")]
public sealed class AzureOpenAITextEmbeddingGeneration : ITextEmbeddingGeneration
{
    private readonly AzureOpenAIClientCore _core;

    /// <summary>
    /// Creates a new <see cref="AzureOpenAITextEmbeddingGeneration"/> client instance using API Key auth.
    /// </summary>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextEmbeddingGeneration(
        OpenAIServiceConfig serviceConfig,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(serviceConfig.DeploymentName);
        Verify.NotNullOrWhiteSpace(serviceConfig.Endpoint);
        Verify.NotNullOrWhiteSpace(serviceConfig.ApiKey);

        this._core = new(serviceConfig.DeploymentName, serviceConfig.Endpoint, serviceConfig.ApiKey, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAITextEmbeddingGeneration)));

        this._core.SetAttributes(serviceConfig);
    }

    /// <summary>
    /// Creates a new <see cref="AzureOpenAITextEmbeddingGeneration"/> client instance supporting AAD auth.
    /// </summary>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="credential">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextEmbeddingGeneration(
        OpenAIServiceConfig serviceConfig,
        TokenCredential credential,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(serviceConfig.DeploymentName);
        Verify.NotNullOrWhiteSpace(serviceConfig.Endpoint);

        this._core = new(serviceConfig.DeploymentName, serviceConfig.Endpoint, credential, httpClient, loggerFactory?.CreateLogger(typeof(AzureOpenAITextEmbeddingGeneration)));

        this._core.SetAttributes(serviceConfig);
    }

    /// <summary>
    /// Creates a new <see cref="AzureOpenAITextEmbeddingGeneration"/> client.
    /// </summary>
    /// <param name="serviceConfig">Service configuration <see cref="OpenAIServiceConfig"/></param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public AzureOpenAITextEmbeddingGeneration(
        OpenAIServiceConfig serviceConfig,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(serviceConfig.DeploymentName);

        this._core = new(serviceConfig.DeploymentName, openAIClient, loggerFactory?.CreateLogger(typeof(AzureOpenAITextEmbeddingGeneration)));

        this._core.SetAttributes(serviceConfig);
    }

    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => this._core.Attributes;

    /// <inheritdoc/>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        this._core.LogActionDetails();
        return this._core.GetEmbeddingsAsync(data, kernel, cancellationToken);
    }
}
