// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;
using OllamaSharp;
using OllamaSharp.Models;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents a embedding generation service using Ollama Original API.
/// </summary>
public sealed class OllamaTextEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    private Dictionary<string, object?> AttributesInternal { get; } = new();
    private readonly OllamaApiClient _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="model">The hosted model.</param>
    /// <param name="baseUri">The base uri including the port where Ollama server is hosted</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the Ollama API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextEmbeddingGenerationService(
        string model,
        Uri baseUri,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);

        this._client = new OllamaApiClient(baseUri, model);

        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextEmbeddingGenerationService"/> class.
    /// </summary>
    /// <param name="model">The hosted model.</param>
    /// <param name="ollamaClient">The Ollama API client.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public OllamaTextEmbeddingGenerationService(
        string model,
        OllamaApiClient ollamaClient,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(model);
        this._client = ollamaClient;
        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc/>
    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var tasks = new List<Task<GenerateEmbeddingResponse>>();
        foreach (var prompt in data)
        {
            tasks.Add(this._client.GenerateEmbeddings(prompt, cancellationToken: cancellationToken));
        }

        await Task.WhenAll(tasks.ToArray()).ConfigureAwait(false);

        return new List<ReadOnlyMemory<float>>(
            tasks.Select(
                task => new ReadOnlyMemory<float>(task.Result.Embedding
                    .Select(@decimal => (float)@decimal).ToArray()
                )
            )
        );
    }
}
