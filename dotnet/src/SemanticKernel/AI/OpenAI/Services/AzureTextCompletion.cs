// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

/// <summary>
/// Azure OpenAI text completion client.
/// </summary>
public sealed class AzureTextCompletion : AzureOpenAIClientAbstract, ITextCompletionClient
{
    /// <summary>
    /// Creates a new AzureTextCompletion client instance
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference</param>
    /// <param name="log">Application logger</param>
    public AzureTextCompletion(string modelId, string endpoint, string apiKey, string apiVersion, ILogger? log = null)
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

    /// <summary>
    /// Creates a completion for the provided prompt and parameters
    /// </summary>
    /// <param name="text">Text to complete</param>
    /// <param name="aiRequestSettings">The request settings for the completion backend</param>
    /// <returns>The completed text.</returns>
    /// <exception cref="AIException">AIException thrown during the request</exception>
    public async Task<string> CompleteAsync(string text, AIRequestSettings aiRequestSettings)
    {
        Verify.NotNull(aiRequestSettings, "Request settings cannot be empty");
        Verify.NotNull(aiRequestSettings.CompleteRequestSettings, "Completion request settings cannot be empty");
        var completeRequestSettings = aiRequestSettings.CompleteRequestSettings;

        var deploymentName = await this.GetDeploymentNameAsync(this._modelId);
        var url = $"{this.Endpoint}/openai/deployments/{deploymentName}/completions?api-version={this.AzureOpenAIApiVersion}";

        this.Log.LogDebug("Sending Azure OpenAI completion request to {0}", url);

        if (completeRequestSettings.MaxTokens < 1)
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidRequest,
                $"MaxTokens {completeRequestSettings.MaxTokens} is not valid, the value must be greater than zero");
        }

        var requestBody = Json.Serialize(new AzureCompletionRequest
        {
            Prompt = text,
            Temperature = completeRequestSettings.Temperature,
            TopP = completeRequestSettings.TopP,
            PresencePenalty = completeRequestSettings.PresencePenalty,
            FrequencyPenalty = completeRequestSettings.FrequencyPenalty,
            MaxTokens = completeRequestSettings.MaxTokens,
            Stop = completeRequestSettings.StopSequences is { Count: > 0 } ? completeRequestSettings.StopSequences : null,
        });


        return await this.ExecuteCompleteRequestAsync(url, requestBody, aiRequestSettings.HttpTimeoutInSeconds);
    }

    #region private ================================================================================

    private readonly string _modelId;

    #endregion
}
