// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

/// <summary>
/// Client to OpenAI.com embedding endpoint, used to generate embeddings.
/// </summary>
public sealed class OpenAITextEmbeddings : IEmbeddingGenerator<string, float>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAITextEmbeddings"/> class.
    /// </summary>
    /// <param name="serviceClient">OpenAI service client.</param>
    /// <param name="modelId">OpenAI model ID</param>
    public OpenAITextEmbeddings(IOpenAIServiceClient serviceClient, string modelId)
    {
        Verify.NotNull(serviceClient, "OpenAI service client is not set to an instance of an object.");
        Verify.NotEmpty(modelId, "The OpenAI model ID cannot be empty");

        this._serviceClient = serviceClient;
        this._modelId = modelId;
    }

    /// <inheritdoc/>
    public async Task<IList<Embedding<float>>> GenerateEmbeddingsAsync(IList<string> data, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(data, "List o strings is not set to an instance of an object.");

        var request = new OpenAIEmbeddingRequest { Model = this._modelId, Input = data };

        var response = await this._serviceClient.CreateEmbeddingAsync(request, cancellationToken);

        return response.Embeddings.Select(e => new Embedding<float>(e.Values.ToArray())).ToList();
    }

    #region private ================================================================================

    /// <summary>
    /// OpenAI service client.
    /// </summary>
    private readonly IOpenAIServiceClient _serviceClient;

    /// <summary>
    /// OpenAI model ID. 
    /// </summary>
    private readonly string _modelId;

    #endregion
}
