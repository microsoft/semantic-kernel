// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http.Headers;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;
public sealed class OpenAIChatCompletion : OpenAIClientAbstract, IChatCompletionClient
{
    // 3P OpenAI REST API endpoint
    private const string OpenaiEndpoint = "https://api.openai.com/v1";

    private readonly string _modelId;

    /// <summary>
    /// Creates a new OpenAIChatCompletion with supplied values.
    /// </summary>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="organization">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="log">Logger</param>
    /// <param name="handlerFactory">Retry handler</param>
    public OpenAIChatCompletion(string modelId, string apiKey, string? organization = null, ILogger? log = null,
        IDelegatingHandlerFactory? handlerFactory = null) :
        base(log, handlerFactory)
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
    /// Creates a new chat completion request for the prompt and settings.
    /// </summary>
    /// <param name="messages">The messages to send.</param>
    /// <param name="requestSettings">Request settings for the chat completion API</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>The completed text</returns>
    /// <exception cref="AIException">AIException thrown during the request</exception>
    public async Task<string> CompleteAsync(JsonArray messages, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(requestSettings, "Completion settings cannot be empty");

        var url = $"{OpenaiEndpoint}/chat/completions";
        this.Log.LogDebug("Sending OpenAI chat completion request to {0}", url);

        if (requestSettings.MaxTokens < 1)
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidRequest,
                $"MaxTokens {requestSettings.MaxTokens} is not valid, the value must be greater than zero");
        }

        var requestBody = Json.Serialize(new OpenAIChatCompletionRequest
        {
            Model = this._modelId,
            Messages = messages,
            Temperature = requestSettings.Temperature,
            TopP = requestSettings.TopP,
            PresencePenalty = requestSettings.PresencePenalty,
            FrequencyPenalty = requestSettings.FrequencyPenalty,
            MaxTokens = requestSettings.MaxTokens,
            Stop = requestSettings.StopSequences is { Count: > 0 } ? requestSettings.StopSequences : "\\n",
        });

        var result = await this.ExecuteCompleteRequestAsync<ChatCompletionResponse>(url, requestBody, cancellationToken);
        if (result.Choices.Count < 1)
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidResponseContent,
                "Completions not found");
        }

        return result.Choices.First().Message.Content;
    }
}
