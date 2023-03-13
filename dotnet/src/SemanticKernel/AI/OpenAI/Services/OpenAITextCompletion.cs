// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

/// <summary>
/// OpenAI text completion service.
/// </summary>
public sealed class OpenAITextCompletion : ITextCompletionClient
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAITextCompletion"/> class.
    /// </summary>
    /// <param name="serviceClient">OpenAI service client.</param>
    /// <param name="modelId">OpenAI model id or deployment name.</param>
    public OpenAITextCompletion(IOpenAIServiceClient serviceClient, string modelId)
    {
        Verify.NotNull(serviceClient, "OpenAI service client is not set to an instance of an object.");
        Verify.NotEmpty(modelId, "The model id cannot be empty, you must provide a model id or a deployment name.");

        this._serviceClient = serviceClient;
        this._modelId = modelId;
    }

    /// <inheritdoc/>
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

        var request = new OpenAICompletionRequest
        {
            Prompt = text,
            Temperature = requestSettings.Temperature,
            TopP = requestSettings.TopP,
            PresencePenalty = requestSettings.PresencePenalty,
            FrequencyPenalty = requestSettings.FrequencyPenalty,
            MaxTokens = requestSettings.MaxTokens,
            Stop = requestSettings.StopSequences is { Count: > 0 } ? requestSettings.StopSequences : null,
        };

        var response = await this._serviceClient.ExecuteCompletionAsync(request, this._modelId, cancellationToken);

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
    /// OpenAI service client.
    /// </summary>
    private readonly IOpenAIServiceClient _serviceClient;

    /// <summary>
    /// OpenAI model id. 
    /// </summary>
    private readonly string _modelId;

    #endregion
}
