// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI.ChatCompletion;

public class AzureChatCompletion : AzureOpenAIClientAbstract, IChatCompletion
{
    private readonly string _modelId;
    private readonly string _chatApiVersion;

    public AzureChatCompletion(
        string modelId,
        string endpoint,
        string apiKey,
        string apiVersion,
        string chatApiVersion,
        ILogger? log = null,
        IDelegatingHandlerFactory? handlerFactory = null
    ) : base(log, handlerFactory)
    {
        Verify.NotEmpty(modelId, "The ID cannot be empty, you must provide a Model ID or a Deployment name.");
        this._modelId = modelId;

        Verify.NotEmpty(endpoint, "The Azure endpoint cannot be empty");
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        this.Endpoint = endpoint.TrimEnd('/');

        Verify.NotEmpty(apiKey, "The Azure API key cannot be empty");
        this.HTTPClient.DefaultRequestHeaders.Add("api-key", apiKey);

        this.AzureOpenAIApiVersion = apiVersion;
        this._chatApiVersion = chatApiVersion;
    }

    /// <inheritdoc/>
    public async Task<string> GenerateMessageAsync(
        ChatHistory chat,
        ChatRequestSettings requestSettings,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(requestSettings, "Completion settings cannot be empty");
        var deploymentName = await this.GetDeploymentNameAsync(this._modelId);
        var url = $"{this.Endpoint}/openai/deployments/{deploymentName}/chat/completions?api-version={this._chatApiVersion}";

        this.Log.LogDebug("Sending Azure OpenAI Chat completion request to {0}", url);

        if (requestSettings.MaxTokens < 1)
        {
            throw new AIException(
                AIException.ErrorCodes.InvalidRequest,
                $"MaxTokens {requestSettings.MaxTokens} is not valid, the value must be greater than zero");
        }

        var requestBody = Json.Serialize(new ChatCompletionRequest
        {
            Model = this._modelId,
            Messages = ToHttpSchema(chat),
            Temperature = requestSettings.Temperature,
            TopP = requestSettings.TopP,
            PresencePenalty = requestSettings.PresencePenalty,
            FrequencyPenalty = requestSettings.FrequencyPenalty,
            MaxTokens = requestSettings.MaxTokens,
            Stop = requestSettings.StopSequences is { Count: > 0 } ? requestSettings.StopSequences : null,
        });

        return await this.ExecuteChatCompletionRequestAsync(url, requestBody, cancellationToken);
    }

    /// <inheritdoc/>
    public ChatHistory CreateNewChat(string? instructions = null)
    {
        return new OpenAIChatHistory(instructions);
    }

    /// <summary>
    /// Map chat data to HTTP schema used with LLM
    /// </summary>
    /// <returns>Returns list of chat messages</returns>
    private static IList<ChatCompletionRequest.Message> ToHttpSchema(ChatHistory chat)
    {
        return chat.Messages
            .Select(msg => new ChatCompletionRequest.Message(msg.AuthorRole, msg.Content))
            .ToList();
    }
}
