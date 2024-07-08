// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
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
        this._chatGenerationEndpoint = new Uri("https://bedrock-runtime.us-east-1.amazonaws.com");
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
        }
    }
    internal async Task<ConverseResponse> ConverseBedrockModelAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, CancellationToken cancellationToken = default)
    {
        var converseRequest = this._ioService.GetConverseRequest(this._modelId, chatHistory, executionSettings);
        return await this._bedrockApi.ConverseAsync(converseRequest, cancellationToken).ConfigureAwait(true);
    }
    internal async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        ConverseResponse response;
        var activity = ModelDiagnostics.StartCompletionActivity(
            this._chatGenerationEndpoint, this._modelId, this._modelProvider, chatHistory, executionSettings);
        try
        {
            response = await this.ConverseBedrockModelAsync(chatHistory, executionSettings ?? new PromptExecutionSettings(), cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            throw;
        }

        IEnumerable<ChatMessageContent> chat = ConvertToMessageContent(response);
        activity?.SetCompletionResponse(chat);
        return chat.ToList();
    }

    public static IEnumerable<ChatMessageContent> ConvertToMessageContent(ConverseResponse response)
    {
        if (response.Output.Message != null)
        {
            var message = response.Output.Message;
            return new[]
            {
                new ChatMessageContent
                {
                    Role = MapRole(message.Role.Value),
                    Items = CreateChatMessageContentItemCollection(message.Content)
                }
            };
        }
        return Enumerable.Empty<ChatMessageContent>();
    }
    private static AuthorRole MapRole(string role)
    {
        return role.ToLowerInvariant() switch
        {
            "user" => AuthorRole.User,
            "assistant" => AuthorRole.Assistant,
            "system" => AuthorRole.System,
            _ => throw new ArgumentOutOfRangeException(nameof(role), $"Invalid role: {role}")
        };
    }
    private static ChatMessageContentItemCollection CreateChatMessageContentItemCollection(List<ContentBlock> contentBlocks)
    {
        var itemCollection = new ChatMessageContentItemCollection();
        foreach (var contentBlock in contentBlocks)
        {
            itemCollection.Add(new TextContent(contentBlock.Text));
        }
        return itemCollection;
    }
}
