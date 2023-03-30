// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI.TextCompletion;

/// <summary>
/// OpenAI text completion service.
/// </summary>
public sealed class OpenAITextCompletion : OpenAIClientAbstract, ITextCompletion
{
    // 3P OpenAI REST API endpoint
    private const string OpenaiEndpoint = "https://api.openai.com/v1/completions";

    private readonly string _modelId;

    /// <summary>
    /// Create a new instance of OpenAI text generation service
    /// </summary>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="organization">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="log">Logger</param>
    /// <param name="handlerFactory">Retry handler</param>
    public OpenAITextCompletion(
        string modelId,
        string apiKey,
        string? organization = null,
        ILogger? log = null,
        IDelegatingHandlerFactory? handlerFactory = null
    ) : base(log, handlerFactory)
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

    /// <summary>
    /// Creates a new completion for the prompt and settings.
    /// </summary>
    /// <param name="text">The prompt to complete.</param>
    /// <param name="requestSettings">Request settings for the completion API</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>The completed text</returns>
    /// <exception cref="AIException">AIException thrown during the request</exception>
    public Task<string> CompleteAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(requestSettings, "Completion settings cannot be empty");
        this.Log.LogDebug("Sending OpenAI completion request to {0}", OpenaiEndpoint);

        if (requestSettings.MaxTokens < 1)
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidRequest,
                $"MaxTokens {requestSettings.MaxTokens} is not valid, the value must be greater than zero");
        }

        var requestBody = Json.Serialize(new OpenAITextCompletionRequest
        {
            Model = this._modelId,
            Prompt = text.NormalizeLineEndings(),
            Temperature = requestSettings.Temperature,
            TopP = requestSettings.TopP,
            PresencePenalty = requestSettings.PresencePenalty,
            FrequencyPenalty = requestSettings.FrequencyPenalty,
            MaxTokens = requestSettings.MaxTokens,
            Stop = requestSettings.StopSequences is { Count: > 0 } ? requestSettings.StopSequences : null,
        });

        return this.ExecuteTextCompletionRequestAsync(OpenaiEndpoint, requestBody, cancellationToken);
    }
}
