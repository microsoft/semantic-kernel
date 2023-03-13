// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;

namespace Microsoft.SemanticKernel.AI.OpenAI.Clients;

/// <summary>
/// AzureOpenAI service client interface.
/// </summary>
public interface IAzureOpenAIServiceClient
{
    /// <summary>
    /// Creates AzureOpenAI embedding.
    /// </summary>
    /// <param name="request">A request to create embedding vector representing input text.</param>
    /// <param name="deploymentName">The deployment name.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The embedding vector.</returns>
    Task<EmbeddingResponse> CreateEmbeddingAsync(EmbeddingRequest request, string deploymentName, CancellationToken cancellationToken);

    /// <summary>
    /// Executes completion.
    /// </summary>
    /// <param name="request">The completion request.</param>
    /// <param name="deploymentName">The deployment name.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The execution result</returns>
    Task<CompletionResponse> ExecuteCompletionAsync(AzureCompletionRequest request, string deploymentName, CancellationToken cancellationToken);

    /// <summary>
    /// Requests AzureOpenAI deployments.
    /// </summary>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The AzureOpenAI deployments.</returns>
    Task<AzureDeployments> GetDeploymentsAsync(CancellationToken cancellationToken);
}
