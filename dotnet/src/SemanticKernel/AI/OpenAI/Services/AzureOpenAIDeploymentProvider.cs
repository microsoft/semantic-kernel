// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services.Deployments;

/// <summary>
/// The Azure OpenAI deployment provider.
/// </summary>
public sealed class AzureOpenAIDeploymentProvider : IAzureOpenAIDeploymentProvider
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIDeploymentProvider"/> class.
    /// </summary>
    /// <param name="serviceClient">Azure OpenAI service client.</param>
    /// <param name="modelNamespace">Azure OpenAI model namespace, usually it's Azure OpenAI endpoint.</param>
    public AzureOpenAIDeploymentProvider(IAzureOpenAIServiceClient serviceClient, string modelNamespace)
    {
        Verify.NotNull(serviceClient, "Azure OpenAI service client is not set to an instance of an object.");
        Verify.NotEmpty(modelNamespace, "The model namespace cannot be empty.");

        this._serviceClient = serviceClient;
        this._modelNamespace = modelNamespace;
    }

    /// <inheritdoc/>
    public async Task<string> GetDeploymentNameAsync(string modelId, CancellationToken cancellationToken)
    {
        string fullModelId = this._modelNamespace + ":" + modelId;

        // If the value is a deployment name
        if (s_deploymentToModel.ContainsKey(fullModelId))
        {
            return modelId;
        }

        // If the value is a model id present in the cache
        if (s_modelToDeployment.TryGetValue(fullModelId, out string modelIdCached))
        {
            return modelIdCached;
        }

        var deployments = await this.GetDeploymentsAsync(cancellationToken);

        this.CacheDeployments(deployments);

        if (s_modelToDeployment.TryGetValue(fullModelId, out string modelIdAfterCache))
        {
            return modelIdAfterCache;
        }

        var modelsAvailable = string.Join(", ", s_modelToDeployment.Keys);
        throw new AIException(
            AIException.ErrorCodes.ModelNotAvailable,
            $"Model '{modelId}' not available on {this._modelNamespace}. " +
            $"Available models: {modelsAvailable}. Deploy the model and restart the application.");
    }

    /// <summary>
    /// Requests AzureOpenAI deployments.
    /// </summary>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The AzureOpenAI deployments.</returns>
    private async Task<AzureDeployments> GetDeploymentsAsync(CancellationToken cancellationToken)
    {
        try
        {
            return await this._serviceClient.GetDeploymentsAsync(cancellationToken);
        }
        catch (Exception e)
        {
            throw new AIException(
                AIException.ErrorCodes.ModelNotAvailable,
                $"Unable to fetch the list of model deployments from Azure.", e);
        }
    }

    /// <summary>
    /// Caches the list of Azure OpenAI deployments in Azure OpenAI.
    /// </summary>
    /// <returns>An async task.</returns>
    /// <exception cref="AIException">AIException thrown during the request.</exception>
    private void CacheDeployments(AzureDeployments deployments)
    {
        lock (s_deploymentToModel)
        {
            foreach (var deployment in deployments.Deployments)
            {
                if (!deployment.IsAvailableDeployment() || string.IsNullOrEmpty(deployment.ModelName) || string.IsNullOrEmpty(deployment.DeploymentName))
                {
                    continue;
                }

                s_deploymentToModel[this._modelNamespace + ":" + deployment.DeploymentName] = deployment.ModelName;
                s_modelToDeployment[this._modelNamespace + ":" + deployment.ModelName] = deployment.DeploymentName;
            }
        }
    }

    #region private ================================================================================

    /// <summary>
    /// Cache to get model by deployment.
    /// </summary>
    private static readonly ConcurrentDictionary<string, string> s_deploymentToModel = new();

    /// <summary>
    /// Cache to get deployment by model.
    /// </summary>
    private static readonly ConcurrentDictionary<string, string> s_modelToDeployment = new();

    /// <summary>
    /// Azure OpenAI service client.
    /// </summary>
    private readonly IAzureOpenAIServiceClient _serviceClient;

    /// <summary>
    /// Azure OpenAI model namespace. 
    /// </summary>
    private readonly string _modelNamespace;

    #endregion
}
