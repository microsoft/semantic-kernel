// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

/// <summary>
/// Azure OpenAI text embedding service.
/// </summary>
public sealed class AzureTextEmbeddings : AzureOpenAIClientAbstract, IEmbeddingGenerator<string, float>
{
    private readonly string _modelId;

    /// <summary>
    /// Creates a new AzureTextEmbeddings client instance
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference</param>
    /// <param name="log">Application logger</param>
    public AzureTextEmbeddings(string modelId, string endpoint, string apiKey, string apiVersion, ILogger? log = null)
        : base(log)
    {
        Verify.NotEmpty(modelId, "The ID cannot be empty, you must provide a Model ID or a Deployment name.");
        this._modelId = modelId;

        Verify.NotEmpty(endpoint, "The Azure endpoint cannot be empty");
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        this.Endpoint = endpoint.TrimEnd('/');

        Verify.NotEmpty(apiKey, "The Azure API key cannot be empty");
        this.HTTPClient.DefaultRequestHeaders.Add("api-key", apiKey);

        this.AzureOpenAIApiVersion = apiVersion;
    }

    /// <inheritdoc/>
    public async Task<IList<Embedding<float>>> GenerateEmbeddingsAsync(IList<string> data)
    {
        var deploymentName = await this.GetDeploymentNameAsync(this._modelId);
        var url = $"{this.Endpoint}/openai/deployments/{deploymentName}/embeddings?api-version={this.AzureOpenAIApiVersion}";

        var embeddings = new List<Embedding<float>>(data.Count);

        for (int i = 0; i < data.Count; i++)
        {
            var requestBody = Json.Serialize(new AzureEmbeddingRequest { Input = new List<string> { data[i] } });
            embeddings.AddRange(await this.ExecuteEmbeddingRequestAsync(url, requestBody));
        }

        return embeddings;
    }
}
