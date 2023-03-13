// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services.Deployments;

/// <summary>
/// The Azure OpenAI deployment provider interface.
/// </summary>
public interface IAzureOpenAIDeploymentProvider
{
    /// <summary>
    /// Returns the deployment name of the model id.
    /// </summary>
    /// <param name="modelId">The model id.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>Name of the deployment for the model ID.</returns>
    Task<string> GetDeploymentNameAsync(string modelId, CancellationToken cancellationToken);
}
