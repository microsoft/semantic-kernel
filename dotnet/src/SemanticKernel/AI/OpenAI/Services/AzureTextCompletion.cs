// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.AI.OpenAI.Services.Deployments;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

/// <summary>
/// Azure OpenAI text completion client.
/// </summary>
public sealed class AzureTextCompletion : ITextCompletionClient
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureTextCompletion"/> class.
    /// </summary>
    /// <param name="serviceClient">Azure OpenAI service client.</param>
    /// <param name="deploymentProvider">Azure OpenAI deployment provider.</param>
    /// <param name="modelId">Azure OpenAI model id or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    public AzureTextCompletion(IAzureOpenAIServiceClient serviceClient, IAzureOpenAIDeploymentProvider deploymentProvider, string modelId)
    {
        Verify.NotNull(serviceClient, "AzureOpenAI service client is not set to an instance of an object.");
        Verify.NotNull(deploymentProvider, "AzureOpenAI deployment provider is not set to an instance of an object.");
        Verify.NotEmpty(modelId, "The model id cannot be empty, you must provide a model id or a deployment name.");

        this._serviceClient = serviceClient;
        this._deploymentProvider = deploymentProvider;
        this._modelId = modelId;
    }

    /// <summary>
    /// Creates a completion for the provided prompt and parameters
    /// </summary>
    /// <param name="text">Text to complete - prompt.</param>
    /// <param name="requestSettings">Request settings for the completion API.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The completed text.</returns>
    /// <exception cref="AIException">AIException thrown during the request</exception>
    public async Task<string> CompleteAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken)
    {
        Verify.NotEmpty(text, "Text cannot be empty");
        Verify.NotNull(requestSettings, "Completion settings cannot be empty");

        if (requestSettings.MaxTokens < 1)
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidRequest,
                $"MaxTokens {requestSettings.MaxTokens} is not valid, the value must be greater than zero");
        }

        var request = new AzureCompletionRequest
        {
            Prompt = text,
            Temperature = requestSettings.Temperature,
            TopP = requestSettings.TopP,
            PresencePenalty = requestSettings.PresencePenalty,
            FrequencyPenalty = requestSettings.FrequencyPenalty,
            MaxTokens = requestSettings.MaxTokens,
            Stop = requestSettings.StopSequences is { Count: > 0 } ? requestSettings.StopSequences : null,
        };

        var deploymentName = await this._deploymentProvider.GetDeploymentNameAsync(this._modelId, cancellationToken);

        var response = await this._serviceClient.ExecuteCompletionAsync(request, deploymentName, cancellationToken);

        if (!response.Completions.Any())
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidResponseContent,
                "Completions not found");
        }

        return response.Completions.First().Text;
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
