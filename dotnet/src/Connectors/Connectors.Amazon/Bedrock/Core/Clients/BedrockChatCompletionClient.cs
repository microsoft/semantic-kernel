// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Connectors.Amazon.Models.AI21;
using Connectors.Amazon.Models.Amazon;
using Connectors.Amazon.Models.Anthropic;
using Connectors.Amazon.Models.Cohere;
using Connectors.Amazon.Models.Meta;
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
    private readonly IBedrockModelIOService<IChatCompletionRequest, IChatCompletionResponse> _ioService;
    private readonly Uri _chatGenerationEndpoint;

    public BedrockChatCompletionClient(string modelId, IAmazonBedrockRuntime bedrockApi)
    {
        this._modelId = modelId;
        this._bedrockApi = bedrockApi;
        this._chatGenerationEndpoint = new Uri("https://bedrock-runtime.us-east-1.amazonaws.com");
        int periodIndex = modelId.IndexOf('.'); //modelId looks like "amazon.titan-embed-text-v1:0"
        string modelProvider = periodIndex >= 0 ? modelId.Substring(0, periodIndex) : modelId;
        this._modelProvider = modelProvider;
        switch (modelProvider)
        {
            case "amazon":
                this._ioService = new AmazonIOService();
                break;
            case "mistral":
                this._ioService = new MistralIOService();
                break;
            case "anthropic":
                this._ioService = new AnthropicIOService();
                break;
            case "ai21":
                this._ioService = new AI21IOService();
                break;
            case "cohere":
                this._ioService = new CohereCommandRIOService();
                break;
            case "meta":
                this._ioService = new MetaIOService();
                break;
            default:
                throw new ArgumentException($"Unsupported model provider: {modelProvider}");
        }
    }
    private async Task<ConverseResponse> ConverseBedrockModelAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, CancellationToken cancellationToken = default)
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
        // for (int requestIndex = 1; ; requestIndex++)
        // {
            ConverseResponse response;
            using (var activity = ModelDiagnostics.StartCompletionActivity(
                       this._chatGenerationEndpoint, this._modelId, this._modelProvider, chatHistory, executionSettings))
            {
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
                // foreach (var message in chat)
                // {
                //     chatHistory.AddMessage(AuthorRole.Assistant, message.Content);
                // }
                activity?.SetCompletionResponse(chat);
                return chat.ToList();
            }
        // }
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

    internal async IAsyncEnumerable<StreamingChatMessageContent> StreamChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        // start completion activity
        // call converse stream async (bedrock API)
        // convert output to Sk's StreamingChatMessageContent
        // yield return the streamed contents
        // activity end streaming
        ConverseStreamResponse response;
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._chatGenerationEndpoint, this._modelId, this._modelProvider, chatHistory, executionSettings);
        try
        {
            try
            {
                response = await this.StreamConverseBedrockModel(chatHistory, executionSettings ?? new PromptExecutionSettings(), cancellationToken).ConfigureAwait(false);
            }
            catch (AmazonBedrockRuntimeException e)
            {
                Console.WriteLine($"ERROR: Can't invoke '{this._modelId}'. Reason: {e.Message}");
                throw;
            }
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            throw;
        }

        List<StreamingChatMessageContent>? streamedContents = activity is not null ? [] : null;
        foreach (var chunk in response.Stream.AsEnumerable())
        {
            if (chunk is ContentBlockDeltaEvent)
            {
                var c = (chunk as ContentBlockDeltaEvent).Delta.Text;
                var content = new StreamingChatMessageContent(AuthorRole.Assistant, c);
                streamedContents?.Add(content);
                yield return content;
            }
        }
        activity?.EndStreaming(streamedContents);
    }
    private async Task<ConverseStreamResponse> StreamConverseBedrockModel(ChatHistory chatHistory, PromptExecutionSettings executionSettings, CancellationToken cancellationToken)
    {
        var converseRequest = this._ioService.GetConverseStreamRequest(this._modelId, chatHistory, executionSettings);
        return await this._bedrockApi.ConverseStreamAsync(converseRequest, cancellationToken).ConfigureAwait(true);
    }
}
