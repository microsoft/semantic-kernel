// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Ollama.Core;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Represents a embedding generation service using Ollama Original API.
/// </summary>
[Experimental("SKEXP0011")]
public sealed class OllamaTextEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    private Dictionary<string, object?> AttributesInternal { get; } = new();

    /// <summary>
    /// Initializes a new instance of the OllamaTextEmbeddingGenerationService class.
    /// </summary>
    /// <param name="model">The Ollama model for the chat completion service.</param>
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

        this.Client = new OllamaClient(
            modelId: model,
            httpRequestFactory: new OllamaHttpRequestFactory(),
#pragma warning disable CA2000
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
#pragma warning restore CA2000
            endpointProvider: new OllamaEndpointProvider(baseUri),
            logger: loggerFactory?.CreateLogger(typeof(OllamaChatCompletionService))
        );

        this.AttributesInternal.Add(AIServiceExtensions.ModelIdKey, model);
    }

    private OllamaClient Client { get; }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this.AttributesInternal;

    /// <inheritdoc/>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        return this.Client.GenerateTextEmbeddingAsync(data, cancellationToken: cancellationToken);
    }
}
