// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Amazon;

/// <summary>
/// Represents a text embeddings generation service using Amazon Bedrock API.
/// </summary>
public class BedrockTextEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    private readonly Dictionary<string, object?> _attributesInternal = [];
    private readonly BedrockTextEmbeddingGenerationClient _embeddingGenerationClient;

    /// <summary>
    /// Initializes an instance of the <see cref="BedrockTextEmbeddingGenerationService" /> using an <see cref="IAmazonBedrockRuntime" />.
    /// </summary>
    /// <param name="modelId">Bedrock model id, see https://docs.aws.amazon.com/bedrock/latest/userguide/models-regions.html</param>
    /// <param name="bedrockRuntime">The <see cref="IAmazonBedrockRuntime"/> instance to be used.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public BedrockTextEmbeddingGenerationService(string modelId, IAmazonBedrockRuntime bedrockRuntime, ILoggerFactory? loggerFactory = null)
    {
        this._embeddingGenerationClient = new BedrockTextEmbeddingGenerationClient(modelId, bedrockRuntime, loggerFactory);
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <summary>
    /// Gets the AI service attributes.
    /// </summary>
    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

    /// <summary>
    /// Generates an embedding from the given <paramref name="data"/>.
    /// </summary>
    /// <param name="data">List of strings to generate embeddings for</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of embeddings</returns>
    /// <remarks>Amazon models can only generate embeddings for one string at a time. Passing multiple strings will result in multiple calls to the model, and could result in hitting rate limits.</remarks>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        return this._embeddingGenerationClient.GenerateEmbeddingsAsync(data, cancellationToken);
    }
}
