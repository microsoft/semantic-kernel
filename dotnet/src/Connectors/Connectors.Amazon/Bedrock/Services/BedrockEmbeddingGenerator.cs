// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;

namespace Microsoft.SemanticKernel.Connectors.Amazon;

/// <summary>
/// Represents a text embeddings generation service using Amazon Bedrock API.
/// </summary>
public sealed class BedrockEmbeddingGenerator : IEmbeddingGenerator<string, Embedding<float>>
{
    private readonly BedrockTextEmbeddingGenerationClient _embeddingGenerationClient;
    private readonly EmbeddingGeneratorMetadata? _metadata;

    /// <summary>
    /// Initializes an instance of the <see cref="BedrockEmbeddingGenerator" /> using an <see cref="IAmazonBedrockRuntime" />.
    /// </summary>
    /// <param name="modelId">Bedrock model id, see https://docs.aws.amazon.com/bedrock/latest/userguide/models-regions.html</param>
    /// <param name="bedrockRuntime">The <see cref="IAmazonBedrockRuntime"/> instance to be used.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have, if supported by the model.</param>
    public BedrockEmbeddingGenerator(string modelId, IAmazonBedrockRuntime bedrockRuntime, ILoggerFactory? loggerFactory = null, int? dimensions = null)
    {
        this._embeddingGenerationClient = new BedrockTextEmbeddingGenerationClient(modelId, bedrockRuntime, loggerFactory);
        this._metadata = new EmbeddingGeneratorMetadata(defaultModelId: modelId, defaultModelDimensions: dimensions);
    }

    /// <inheritdoc />
    public async Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(IEnumerable<string> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
    {
        var result = await this._embeddingGenerationClient.GenerateEmbeddingsAsync(values.ToList(), cancellationToken).ConfigureAwait(false);
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
            null;
    }
}
