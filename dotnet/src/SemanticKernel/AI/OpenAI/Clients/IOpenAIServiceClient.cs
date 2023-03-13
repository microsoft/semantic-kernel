// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;

namespace Microsoft.SemanticKernel.AI.OpenAI.Clients;

/// <summary>
/// OpenAI service client interface.
/// </summary>
public interface IOpenAIServiceClient
{
    /// <summary>
    /// Creates OpenAI embedding.
    /// </summary>
    /// <param name="request">A request to create embedding vector representing input text.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The embedding vector.</returns>
    Task<EmbeddingResponse> CreateEmbeddingAsync(OpenAIEmbeddingRequest request, CancellationToken cancellationToken);

    /// <summary>
    /// Executes completion.
    /// </summary>
    /// <param name="request">The completion request.</param>
    /// <param name="modelId">The deployment name.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The execution result</returns>
    Task<CompletionResponse> ExecuteCompletionAsync(OpenAICompletionRequest request, string modelId, CancellationToken cancellationToken);
}
