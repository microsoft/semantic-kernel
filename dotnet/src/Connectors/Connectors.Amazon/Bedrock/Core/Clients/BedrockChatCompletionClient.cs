// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Bedrock.Core;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Represents a client for interacting with the chat completion through Bedrock.
/// </summary>
/// <typeparam name="TRequest"> Request object which is an IChatCompletionRequest. </typeparam>
/// <typeparam name="TResponse"> Response object which is an IChatCompletionResponse. </typeparam>
public class BedrockChatCompletionClient<TRequest, TResponse>
    where TRequest : IChatCompletionRequest
    where TResponse : IChatCompletionResponse
{
    private readonly string _modelId;
    private readonly string _modelProvider;
    private readonly IAmazonBedrockRuntime _bedrockApi;
    private readonly IBedrockModelIOService _ioService;
    private Uri? _chatGenerationEndpoint;

    /// <summary>
    /// Builds the client object and registers the model input-output service given the user's passed in model ID.
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="bedrockApi"></param>
    /// <exception cref="ArgumentException"></exception>
    protected BedrockChatCompletionClient(string modelId, IAmazonBedrockRuntime bedrockApi)
    {
        this._modelId = modelId;
        this._bedrockApi = bedrockApi;
        this._ioService = new BedrockClientIOService().GetIOService(modelId);
        this._modelProvider = new BedrockClientIOService().GetModelProvider(modelId);
    }
    /// <summary>
    /// Builds the convert request body given the model ID (as stored in ioService object) and calls the ConverseAsync Bedrock Runtime action to get the result.
    /// </summary>
    /// <param name="converseRequest"> The converse request for ConverseAsync bedrock runtime action. </param>
    /// <param name="cancellationToken"> A cancellation token to cancel the operation. </param>
    /// <returns></returns>
    private async Task<ConverseResponse> ConverseBedrockModelAsync(
        ConverseRequest converseRequest,
        CancellationToken cancellationToken = default)
    {
        string? text = converseRequest.Messages?[^1]?.Content?[0]?.Text;
        if (string.IsNullOrWhiteSpace(text))
        {
            throw new ArgumentException("Did not enter proper chat completion message. Text was null or whitespace.");
        }
        return await this._bedrockApi.ConverseAsync(converseRequest, cancellationToken).ConfigureAwait(true);
    }
    internal async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrEmpty(chatHistory);
        ConverseRequest converseRequest = this._ioService.GetConverseRequest(this._modelId, chatHistory, executionSettings);
        var regionEndpoint = this._bedrockApi.DetermineServiceOperationEndpoint(converseRequest).URL;
        this._chatGenerationEndpoint = new Uri(regionEndpoint);
        ConverseResponse response;
        using (var activity = ModelDiagnostics.StartCompletionActivity(
                   this._chatGenerationEndpoint, this._modelId, this._modelProvider, chatHistory, executionSettings))
        {
            try
            {
                response = await this.ConverseBedrockModelAsync(converseRequest, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (activity is not null)
            {
                activity.SetError(ex);
                throw;
            }
            IEnumerable<ChatMessageContent> chat = ConvertToMessageContent(response);
            IReadOnlyList<ChatMessageContent> chatMessagesList = chat.ToList();
            activity?.SetCompletionResponse(chatMessagesList);
            return chatMessagesList;
        }
    }
    /// <summary>
    /// Converts the ConverseResponse object as outputted by the Bedrock Runtime API call to a ChatMessageContent for the Semantic Kernel.
    /// </summary>
    /// <param name="response"> ConverseResponse object outputted by Bedrock. </param>
    /// <returns></returns>
    private static IEnumerable<ChatMessageContent> ConvertToMessageContent(ConverseResponse response)
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
        return role switch
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

    // Order of operations:
    // 1. Start completion activity with semantic kernel
    // 2. Call converse stream async with bedrock API
    // 3. Convert output to semantic kernel's StreamingChatMessageContent
    // 4. Yield return the streamed contents
    // 5. End streaming activity with kernel
    internal async IAsyncEnumerable<StreamingChatMessageContent> StreamChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var converseStreamRequest = this._ioService.GetConverseStreamRequest(this._modelId, chatHistory, executionSettings);
        var regionEndpoint = this._bedrockApi.DetermineServiceOperationEndpoint(converseStreamRequest).URL;
        this._chatGenerationEndpoint = new Uri(regionEndpoint);
        ConverseStreamResponse response;
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._chatGenerationEndpoint, this._modelId, this._modelProvider, chatHistory, executionSettings);
        try
        {
            try
            {
                response = await this.StreamConverseBedrockModelAsync(chatHistory, executionSettings, cancellationToken).ConfigureAwait(false);
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
                var c = (chunk as ContentBlockDeltaEvent)?.Delta.Text;
                var content = new StreamingChatMessageContent(AuthorRole.Assistant, c);
                streamedContents?.Add(content);
                yield return content;
            }
        }
        activity?.EndStreaming(streamedContents);
    }
    private async Task<ConverseStreamResponse> StreamConverseBedrockModelAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        var converseRequest = this._ioService.GetConverseStreamRequest(this._modelId, chatHistory, executionSettings);
        return await this._bedrockApi.ConverseStreamAsync(converseRequest, cancellationToken).ConfigureAwait(true);
    }
}
