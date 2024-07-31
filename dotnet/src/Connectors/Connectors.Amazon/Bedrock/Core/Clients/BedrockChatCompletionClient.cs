// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Runtime.CompilerServices;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Bedrock.Core;
using Connectors.Amazon.Models;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Represents a client for interacting with the chat completion through Bedrock.
/// </summary>
internal sealed class BedrockChatCompletionClient
{
    private readonly string _modelId;
    private readonly string _modelProvider;
    private readonly IAmazonBedrockRuntime _bedrockApi;
    private readonly IBedrockModelIOService _ioService;
    private readonly BedrockClientUtilities _clientUtilities;
    private Uri? _chatGenerationEndpoint;

    /// <summary>
    /// Builds the client object and registers the model input-output service given the user's passed in model ID.
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="bedrockApi"></param>
    /// <exception cref="ArgumentException"></exception>
    public BedrockChatCompletionClient(string modelId, IAmazonBedrockRuntime bedrockApi)
    {
        var clientService = new BedrockClientIOService();
        this._modelId = modelId;
        this._bedrockApi = bedrockApi;
        this._ioService = clientService.GetIOService(modelId);
        this._modelProvider = clientService.GetModelProvider(modelId);
        this._clientUtilities = new BedrockClientUtilities();
    }
    /// <summary>
    /// Generates a chat message based on the provided chat history and execution settings.
    /// </summary>
    /// <param name="chatHistory">The chat history to use for generating the chat message.</param>
    /// <param name="executionSettings">The execution settings for the chat generation.</param>
    /// <param name="kernel">The Semantic Kernel instance.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The generated chat message.</returns>
    /// <exception cref="ArgumentException">Thrown when the chat history is null or empty.</exception>
    /// <exception cref="Exception">Thrown when an error occurs during the chat generation process.</exception>
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
        ConverseResponse? response = null;
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._chatGenerationEndpoint, this._modelId, this._modelProvider, chatHistory, executionSettings);
        ActivityStatusCode activityStatus;
        try
        {
            response = await this._bedrockApi.ConverseAsync(converseRequest, cancellationToken).ConfigureAwait(false);
            if (activity is not null)
            {
                activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
                activity.SetStatus(activityStatus);
                activity.SetPromptTokenUsage(response.Usage.InputTokens);
                activity.SetCompletionTokenUsage(response.Usage.OutputTokens);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"ERROR: Can't converse with '{this._modelId}'. Reason: {ex.Message}");
            if (activity is not null)
            {
                activity.SetError(ex);
                if (response != null)
                {
                    activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
                    activity.SetStatus(activityStatus);
                    activity.SetPromptTokenUsage(response.Usage.InputTokens);
                    activity.SetCompletionTokenUsage(response.Usage.OutputTokens);
                }
                else
                {
                    // If response is null, set a default status or leave it unset
                    activity.SetStatus(ActivityStatusCode.Error); // or ActivityStatusCode.Unset
                }
            }
            throw;
        }
        IReadOnlyList<ChatMessageContent> chatMessages = this.ConvertToMessageContent(response).ToList();
        activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
        activity?.SetStatus(activityStatus);
        activity?.SetCompletionResponse(chatMessages, response.Usage.InputTokens, response.Usage.OutputTokens);
        return chatMessages;
    }
    /// <summary>
    /// Converts the ConverseResponse object as outputted by the Bedrock Runtime API call to a ChatMessageContent for the Semantic Kernel.
    /// </summary>
    /// <param name="response"> ConverseResponse object outputted by Bedrock. </param>
    /// <returns></returns>
    private ChatMessageContent[] ConvertToMessageContent(ConverseResponse response)
    {
        if (response.Output.Message == null)
        {
            return [];
        }
        var message = response.Output.Message;
        return new[]
        {
            new ChatMessageContent
            {
                Role = this._clientUtilities.MapConversationRoleToAuthorRole(message.Role.Value),
                Items = CreateChatMessageContentItemCollection(message.Content)
            }
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
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var converseStreamRequest = this._ioService.GetConverseStreamRequest(this._modelId, chatHistory, executionSettings);
        var regionEndpoint = this._bedrockApi.DetermineServiceOperationEndpoint(converseStreamRequest).URL;
        this._chatGenerationEndpoint = new Uri(regionEndpoint);
        ConverseStreamResponse? response = null;
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._chatGenerationEndpoint, this._modelId, this._modelProvider, chatHistory, executionSettings);
        ActivityStatusCode activityStatus;
        try
        {
            response = await this._bedrockApi.ConverseStreamAsync(converseStreamRequest, cancellationToken).ConfigureAwait(false);
            if (activity is not null)
            {
                activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
                activity.SetStatus(activityStatus);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"ERROR: Can't converse stream with '{this._modelId}'. Reason: {ex.Message}");
            if (activity is not null)
            {
                activity.SetError(ex);
                if (response != null)
                {
                    activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
                    activity.SetStatus(activityStatus);
                }
                else
                {
                    // If response is null, set a default status or leave it unset
                    activity.SetStatus(ActivityStatusCode.Error); // or ActivityStatusCode.Unset
                }
            }
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
        activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
        activity?.SetStatus(activityStatus);
        activity?.EndStreaming(streamedContents);
    }
}
