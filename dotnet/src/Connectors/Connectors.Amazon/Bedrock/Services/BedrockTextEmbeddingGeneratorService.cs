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
/// Represents a chat completion service using Amazon Bedrock API.
/// </summary>
public class BedrockTextEmbeddingGenerationService : ITextEmbeddingGenerationService
{
    private readonly Dictionary<string, object?> _attributesInternal = [];
    private readonly BedrockTextEmbeddingGenerationClient _embeddingGenerationClient;

    /// <summary>
    /// Initializes an instance of the <see cref="BedrockChatCompletionService" /> using an <see cref="IAmazonBedrockRuntime" />.
    /// </summary>
    /// <param name="modelId">Bedrock model id, see https://docs.aws.amazon.com/bedrock/latest/userguide/models-regions.html</param>
    /// <param name="bedrockRuntime">The <see cref="IAmazonBedrockRuntime"/> instance to be used.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public BedrockTextEmbeddingGenerationService(string modelId, IAmazonBedrockRuntime bedrockRuntime, ILoggerFactory? loggerFactory = null)
    {
        this._embeddingGenerationClient = new BedrockTextEmbeddingGenerationClient(modelId, bedrockRuntime, loggerFactory);
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        return this._embeddingGenerationClient.GenerateEmbeddingsAsync(data, cancellationToken);
    }
}
