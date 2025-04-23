// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
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
    private readonly IBedrockChatCompletionService _ioChatService;
    private Uri? _chatGenerationEndpoint;
    private readonly ILogger _logger;

    /// <summary>
    /// Builds the client object and registers the model input-output service given the user's passed in model ID.
    /// </summary>
    /// <param name="modelId">The model ID for the client.</param>
    /// <param name="bedrockRuntime">The <see cref="IAmazonBedrockRuntime"/> instance to be used for Bedrock runtime actions.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal BedrockChatCompletionClient(string modelId, IAmazonBedrockRuntime bedrockRuntime, ILoggerFactory? loggerFactory = null)
    {
        var serviceFactory = new BedrockServiceFactory();
        this._modelId = modelId;
        this._bedrockRuntime = bedrockRuntime;
        this._ioChatService = serviceFactory.CreateChatCompletionService(modelId);
        this._modelProvider = serviceFactory.GetModelProviderAndName(modelId).modelProvider;
        this._logger = loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Generates a chat message based on the provided chat history and execution settings.
    /// </summary>
    /// <param name="chatHistory">The chat history to use for generating the chat message.</param>
    /// <param name="executionSettings">The execution settings for the chat completion.</param>
    /// <param name="kernel">The Semantic Kernel instance.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The generated chat message.</returns>
    /// <exception cref="ArgumentNullException">Thrown when the chat history is null.</exception>
    /// <exception cref="ArgumentException">Thrown when the chat is empty.</exception>
    /// <exception cref="InvalidOperationException">Thrown when response content is not available.</exception>
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
                activityStatus = BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
                activity.SetStatus(activityStatus);
                activity.SetInputTokensUsage(response?.Usage?.InputTokens ?? default);
                activity.SetOutputTokensUsage(response?.Usage?.OutputTokens ?? default);
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
                    activityStatus = BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
                    activity.SetStatus(activityStatus);
                    activity.SetInputTokensUsage(response?.Usage?.InputTokens ?? default);
                    activity.SetOutputTokensUsage(response?.Usage?.OutputTokens ?? default);
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
            throw new InvalidOperationException("Response failed");
        }
        IReadOnlyList<ChatMessageContent> chatMessages = this.ConvertToMessageContent(response).ToList();
        activityStatus = BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
        activity?.SetStatus(activityStatus);
        activity?.SetCompletionResponse(chatMessages, response.Usage.InputTokens, response.Usage.OutputTokens);
        return chatMessages;
    }

    /// <summary>
    /// Converts the ConverseResponse object as outputted by the Bedrock Runtime API call to a ChatMessageContent for the Semantic Kernel.
    /// </summary>
    /// <param name="response"> ConverseResponse object outputted by Bedrock. </param>
    /// <returns>List of ChatMessageContent objects</returns>
    private ChatMessageContent[] ConvertToMessageContent(ConverseResponse response)
    {
        if (response.Output.Message == null)
        {
            return [];
        }
        var message = response.Output.Message;
        return
        [
            new ChatMessageContent
            {
                Role = BedrockClientUtilities.MapConversationRoleToAuthorRole(message.Role.Value),
                Items = CreateChatMessageContentItemCollection(message.Content),
                InnerContent = response
            }
        ];
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
                activityStatus = BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
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
                    activityStatus = BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
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
        await foreach (var chunk in response.Stream.ConfigureAwait(false))
        {
            if (chunk is ContentBlockDeltaEvent deltaEvent)
            {
                // Convert output to semantic kernel's StreamingChatMessageContent
                var c = deltaEvent?.Delta.Text;
                var content = new StreamingChatMessageContent(AuthorRole.Assistant, c, deltaEvent);
                streamedContents?.Add(content);
                yield return content;
            }
        }

        // End streaming activity with kernel
        activityStatus = BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
        activity?.SetStatus(activityStatus);
        activity?.EndStreaming(streamedContents);
    }
}
