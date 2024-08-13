// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Runtime.CompilerServices;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
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
    private readonly IAmazonBedrockRuntime _bedrockRuntime;
    private readonly IBedrockChatCompletionIOService _ioChatService;
    private readonly BedrockClientUtilities _clientUtilities;
    private Uri? _chatGenerationEndpoint;
    private readonly ILogger _logger;

    /// <summary>
    /// Builds the client object and registers the model input-output service given the user's passed in model ID.
    /// </summary>
    /// <param name="modelId">The model ID for the client.</param>
    /// <param name="bedrockRuntime">The IAmazonBedrockRuntime object to be used for Bedrock runtime actions.</param>
    /// <param name="loggerFactory">Logger for error output.</param>
    /// <exception cref="ArgumentException"></exception>
    internal BedrockChatCompletionClient(string modelId, IAmazonBedrockRuntime bedrockRuntime, ILoggerFactory? loggerFactory = null)
    {
        var clientService = new BedrockClientIOService();
        this._modelId = modelId;
        this._bedrockRuntime = bedrockRuntime;
        this._ioChatService = clientService.GetChatIOService(modelId);
        this._modelProvider = clientService.GetModelProviderAndName(modelId).modelProvider;
        this._clientUtilities = new BedrockClientUtilities();
        this._logger = loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance;
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
        ConverseRequest converseRequest = this._ioChatService.GetConverseRequest(this._modelId, chatHistory, executionSettings);
        var regionEndpoint = this._bedrockRuntime.DetermineServiceOperationEndpoint(converseRequest).URL;
        this._chatGenerationEndpoint = new Uri(regionEndpoint);
        ConverseResponse? response = null;
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._chatGenerationEndpoint, this._modelId, this._modelProvider, chatHistory, executionSettings);
        ActivityStatusCode activityStatus;
        try
        {
            response = await this._bedrockRuntime.ConverseAsync(converseRequest, cancellationToken).ConfigureAwait(false);
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
            this._logger.LogError(ex, "Can't converse with '{ModelId}'. Reason: {Error}", this._modelId, ex.Message);
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
        if ((response == null) || response.Output == null || response.Output.Message == null)
        {
            throw new ArgumentException("Response failed");
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

    internal async IAsyncEnumerable<StreamingChatMessageContent> StreamChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // Set up variables for starting completion activity
        var converseStreamRequest = this._ioChatService.GetConverseStreamRequest(this._modelId, chatHistory, executionSettings);
        var regionEndpoint = this._bedrockRuntime.DetermineServiceOperationEndpoint(converseStreamRequest).URL;
        this._chatGenerationEndpoint = new Uri(regionEndpoint);
        ConverseStreamResponse? response = null;

        // Start completion activity with semantic kernel
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._chatGenerationEndpoint, this._modelId, this._modelProvider, chatHistory, executionSettings);
        ActivityStatusCode activityStatus;
        try
        {
            // Call converse stream async with bedrock API
            response = await this._bedrockRuntime.ConverseStreamAsync(converseStreamRequest, cancellationToken).ConfigureAwait(false);
            if (activity is not null)
            {
                activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
                activity.SetStatus(activityStatus);
            }
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Can't converse stream with '{ModelId}'. Reason: {Error}", this._modelId, ex.Message);
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
                // Convert output to semantic kernel's StreamingChatMessageContent
                var c = (chunk as ContentBlockDeltaEvent)?.Delta.Text;
                var content = new StreamingChatMessageContent(AuthorRole.Assistant, c);
                streamedContents?.Add(content);
                yield return content;
            }
        }

        // End streaming activity with kernel
        activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
        activity?.SetStatus(activityStatus);
        activity?.EndStreaming(streamedContents);
    }
}
