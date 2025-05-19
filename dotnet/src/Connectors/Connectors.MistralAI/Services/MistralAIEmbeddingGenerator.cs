// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.MistralAI;

/// <summary>
/// Mistral AI embedding generator service.
/// </summary>
public sealed class MistralAIEmbeddingGenerator : IEmbeddingGenerator<string, Embedding<float>>
{
    private readonly MistralClient _client;
    private readonly EmbeddingGeneratorMetadata? _metadata;

    /// <summary>
    /// Initializes a new instance of the <see cref="MistralAIEmbeddingGenerator"/> class.
    /// </summary>
    /// <param name="modelId">The Mistral modelId for the text generation service.</param>
    /// <param name="apiKey">API key for accessing the MistralAI service.</param>
    /// <param name="endpoint">Optional uri endpoint including the port where MistralAI server is hosted. Default is https://api.mistral.ai.</param>
    /// <param name="httpClient">Optional HTTP client to be used for communication with the MistralAI API.</param>
    /// <param name="loggerFactory">Optional logger factory to be used for logging.</param>
    public MistralAIEmbeddingGenerator(
        string modelId,
        string apiKey,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        this._client = new MistralClient(
            modelId: modelId,
            endpoint: endpoint ?? httpClient?.BaseAddress,
            apiKey: apiKey,
            httpClient: HttpClientProvider.GetHttpClient(httpClient),
            logger: loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance
        );

        this._metadata = new EmbeddingGeneratorMetadata(defaultModelId: modelId);
    }

    /// <inheritdoc />
    public async Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(
        IEnumerable<string> values,
        EmbeddingGenerationOptions? options = null,
        CancellationToken cancellationToken = default)
    {
        var result = await this._client.GenerateEmbeddingsAsync(values.ToList(), cancellationToken).ConfigureAwait(false);
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
            serviceKey is null ? null :
            serviceType.IsInstanceOfType(this) ? this :
            serviceType == typeof(EmbeddingGeneratorMetadata) ? this._metadata :
            null;
    }
}
