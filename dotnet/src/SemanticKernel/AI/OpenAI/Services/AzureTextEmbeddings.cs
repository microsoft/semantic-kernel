// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.AI.OpenAI.Services.Deployments;
using Microsoft.SemanticKernel.Diagnostics;
using static Microsoft.SemanticKernel.AI.OpenAI.HttpSchema.EmbeddingResponse;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

/// <summary>
/// Azure OpenAI text embedding service.
/// </summary>
public sealed class AzureTextEmbeddings : IEmbeddingGenerator<string, float>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureTextEmbeddings"/> class.
    /// </summary>
    /// <param name="serviceClient">Azure OpenAI service client.</param>
    /// <param name="deploymentProvider">Azure OpenAI deployment provider.</param>
    /// <param name="modelId">Azure OpenAI model id or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    public AzureTextEmbeddings(IAzureOpenAIServiceClient serviceClient, IAzureOpenAIDeploymentProvider deploymentProvider, string modelId)
    {
        Verify.NotNull(serviceClient, "AzureOpenAI service client is not set to an instance of an object.");
        Verify.NotNull(deploymentProvider, "AzureOpenAI deployment provider is not set to an instance of an object.");
        Verify.NotEmpty(modelId, "The model id cannot be empty, you must provide a model id or a deployment name.");

        this._serviceClient = serviceClient;
        this._deploymentProvider = deploymentProvider;
        this._modelId = modelId;
    }

    /// <inheritdoc/>
    public async Task<IList<Embedding<float>>> GenerateEmbeddingsAsync(IList<string> data, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(data, "List o strings is not set to an instance of an object.");

        var deploymentName = await this._deploymentProvider.GetDeploymentNameAsync(this._modelId, cancellationToken);

        var result = new List<EmbeddingResponseIndex>(data.Count);

        for (int i = 0; i < data.Count; i++)
        {
            var request = new AzureEmbeddingRequest { Input = new List<string> { data[i] } };

            var response = await this._serviceClient.CreateEmbeddingAsync(request, deploymentName, cancellationToken);

            result.AddRange(response.Embeddings);
        }

        return result.Select(e => new Embedding<float>(e.Values.ToArray())).ToList(); ;
    }

    #region private ================================================================================

    /// <summary>
    /// Azure OpenAI service client.
    /// </summary>
    private readonly IAzureOpenAIServiceClient _serviceClient;

    /// <summary>
    /// Azure OpenAI deployment provider.
    /// </summary>
    private readonly IAzureOpenAIDeploymentProvider _deploymentProvider;

    /// <summary>
    /// Azure OpenAI model id. 
    /// </summary>
    private readonly string _modelId;

    #endregion
}
