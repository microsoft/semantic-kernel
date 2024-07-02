// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Connectors.Amazon.Models.Amazon;
using Connectors.Amazon.Models.Mistral;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

public class BedrockChatCompletionClient<TRequest, TResponse>
    where TRequest : IChatCompletionRequest
    where TResponse : IChatCompletionResponse
{
    private readonly string _modelId;
    private readonly string _modelProvider;
    private readonly IAmazonBedrockRuntime _bedrockApi;
    private readonly IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse> _ioService;
    private readonly Uri _chatGenerationEndpoint;

    public BedrockChatCompletionClient(string modelId, IAmazonBedrockRuntime bedrockApi)
    {
        this._modelId = modelId;
        this._bedrockApi = bedrockApi;
        this._chatGenerationEndpoint = new Uri("something");
        int periodIndex = modelId.IndexOf('.'); //modelId looks like "amazon.titan-embed-text-v1"
        string modelProvider = periodIndex >= 0 ? modelId.Substring(0, periodIndex) : modelId;
        this._modelProvider = modelProvider;
        switch (modelProvider)
        {
            case "amazon":
                this._ioService = new AmazonIoService();
                break;
            case "mistral":
                this._ioService = new MistralIoService();
                break;
            default:
                throw new Exception("Error: model not found");
                break;
        }
    }
    internal async Task<IChatCompletionResponse> ConverseBedrockModelAsync(ChatHistory chatHistory, PromptExecutionSettings executionSettings, CancellationToken cancellationToken = default)
    {
        // var requestBody = this._ioService.GetApiRequestBody(prompt, executionSettings);
        var converseRequest = new ConverseRequest
        {
            ModelId = this._modelId,
            Messages = chatHistory.Select(messageContent => new Message
            {
                Content = new List<ContentBlock>
                {
                    new ContentBlock
                    {
                        Text = messageContent.Content
                    }
                }
            }).ToList()
        };
        var response = await this._bedrockApi.ConverseAsync(converseRequest, cancellationToken).ConfigureAwait(true);
        return this._ioService.ConvertApiResponse(response);
    }
    internal async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        IChatCompletionResponse responses;
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._chatGenerationEndpoint, this._modelId, this._modelProvider, chatHistory, executionSettings);
        try
        {
            responses = await this.ConverseBedrockModelAsync(chatHistory, executionSettings ?? new PromptExecutionSettings(), cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            throw;
        }
        return activity?.SetCompletionResponse(responses); //parse msg content, convert to list
    }
    // private ConversationRole GetConversationRole(AuthorRole authorRole)
    // {
    //     return authorRole switch
    //     {
    //         AuthorRole.User => new ConversationRole("user"),
    //         AuthorRole.Assistant => new ConversationRole("assistant"),
    //         _ => throw new ArgumentOutOfRangeException(nameof(authorRole), $"Unknown author role: {authorRole}")
    //     };
    // }
}
