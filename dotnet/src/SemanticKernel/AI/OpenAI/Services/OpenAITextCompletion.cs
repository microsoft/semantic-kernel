// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Headers;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

/// <summary>
/// OpenAI text completion service.
/// </summary>
public sealed class OpenAITextCompletion : OpenAIClientAbstract, ITextCompletionClient
{
    // 3P OpenAI REST API endpoint
    private const string OpenaiEndpoint = "https://api.openai.com/v1";

    private readonly string _modelId;

    /// <summary>
    /// Creates a new OpenAITextCompletion with supplied values.
    /// </summary>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="organization">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="log">Logger</param>
    public OpenAITextCompletion(string modelId, string apiKey, string? organization = null, ILogger? log = null) :
        base(log)
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
    /// <returns>The completed text</returns>
    /// <exception cref="AIException">AIException thrown during the request</exception>
    public async Task<string> CompleteAsync(string text, CompleteRequestSettings requestSettings)
    {
        Verify.NotNull(requestSettings, "Completion settings cannot be empty");

        var url = $"{OpenaiEndpoint}/engines/{this._modelId}/completions";
        this.Log.LogDebug("Sending OpenAI completion request to {0}", url);

        if (requestSettings.MaxTokens < 1)
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidRequest,
                $"MaxTokens {requestSettings.MaxTokens} is not valid, the value must be greater than zero");
        }

        var requestBody = Json.Serialize(new OpenAICompletionRequest
        {
            Prompt = text,
            Temperature = requestSettings.Temperature,
            TopP = requestSettings.TopP,
            PresencePenalty = requestSettings.PresencePenalty,
            FrequencyPenalty = requestSettings.FrequencyPenalty,
            MaxTokens = requestSettings.MaxTokens,
            Stop = requestSettings.StopSequences is { Count: > 0 } ? requestSettings.StopSequences : null,
        });

        return await this.ExecuteCompleteRequestAsync(url, requestBody);
    }
}
