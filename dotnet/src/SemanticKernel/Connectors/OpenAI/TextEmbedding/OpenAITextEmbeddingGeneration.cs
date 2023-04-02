// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI.TextEmbedding;

/// <summary>
/// Client to OpenAI.com embedding endpoint, used to generate embeddings.
/// </summary>
public sealed class OpenAITextEmbeddingGeneration : OpenAIClientAbstract, IEmbeddingGeneration<string, float>
{
    // 3P OpenAI REST API endpoint
    private const string OpenaiEndpoint = "https://api.openai.com/v1";
    private const string OpenaiEmbeddingEndpoint = $"{OpenaiEndpoint}/embeddings";

    private readonly string _modelId;

    /// <summary>
    /// Create an instance of OpenAI embeddings endpoint client
    /// </summary>
    /// <param name="modelId">OpenAI embedding model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">Optional OpenAI organization ID, usually required only if your account belongs to multiple organizations</param>
    /// <param name="log">Application logger</param>
    /// <param name="handlerFactory">Retry handler factory for HTTP requests.</param>
    public OpenAITextEmbeddingGeneration(string modelId, string apiKey, string? organization = null, ILogger? log = null,
        IDelegatingHandlerFactory? handlerFactory = null)
        : base(log, handlerFactory)
    {
        Verify.NotEmpty(modelId, "The OpenAI model ID cannot be empty");
        this._modelId = modelId;

        Verify.NotEmpty(apiKey, "The OpenAI API key cannot be empty");
        this.HTTPClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);

        if (!string.IsNullOrEmpty(organization))
        {
            this.HTTPClient.DefaultRequestHeaders.Add("OpenAI-Organization", organization);
        }
    }

    /// <inheritdoc/>
    public async Task<IList<Embedding<float>>> GenerateEmbeddingsAsync(IList<string> data)
    {
        var requestBody = Json.Serialize(new OpenAITextEmbeddingRequest { Model = this._modelId, Input = data, });

        return await this.ExecuteTextEmbeddingRequestAsync(OpenaiEmbeddingEndpoint, requestBody);
    }
}
