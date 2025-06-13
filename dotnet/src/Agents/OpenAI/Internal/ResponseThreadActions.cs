// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.FunctionCalling;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Internal;

/// <summary>
/// Actions associated with an OpeAI Responses thread.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class ResponseThreadActions
{
    internal static async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        OpenAIResponseAgent agent,
        ChatHistory history,
        AgentThread agentThread,
        AgentInvokeOptions options,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var responseAgentThread = agentThread as OpenAIResponseAgentThread;

        var overrideHistory = history;
        if (!agent.StoreEnabled)
        {
            // Use the thread chat history
            overrideHistory = [.. GetChatHistory(agentThread)];
        }

        var creationOptions = ResponseCreationOptionsFactory.CreateOptions(agent, agentThread, options);

        var inputItems = overrideHistory.Select(c => c.ToResponseItem()).ToList();
        FunctionCallsProcessor functionProcessor = new();
        FunctionChoiceBehaviorOptions functionOptions = new() { AllowConcurrentInvocation = true, AllowParallelCalls = true, RetainArgumentTypes = true };
        for (int requestIndex = 0; ; requestIndex++)
        {
            // Create a response using the OpenAI Responses API
            var clientResult = await agent.Client.CreateResponseAsync(inputItems, creationOptions, cancellationToken).ConfigureAwait(false);
            var response = clientResult.Value;
            ThrowIfIncompleteOrFailed(agent, response);

            // Update the response ID in the creation options
            if (responseAgentThread is not null)
            {
                creationOptions.PreviousResponseId = response.Id;
                responseAgentThread.ResponseId = response.Id;
            }
            else
            {
                inputItems.AddRange(response.OutputItems);
            }

            var message = response.ToChatMessageContent();
            overrideHistory.Add(message);
            yield return message;

            // Reached maximum auto invocations
            if (requestIndex == MaximumAutoInvokeAttempts)
            {
                break;
            }

            // Check if there are any functions to invoke.
            var functionCalls = response.OutputItems
                .OfType<FunctionCallResponseItem>()
                .Select(f => f.ToFunctionCallContent())
                .ToList();
            if (functionCalls.Count == 0)
            {
                break;
            }

            // Invoke functions and create function output items for results
            FunctionResultContent[] functionResults =
                await functionProcessor.InvokeFunctionCallsAsync(
                    message,
                    (_) => true,
                    functionOptions,
                    options.GetKernel(agent),
                    isStreaming: false,
                    cancellationToken).ToArrayAsync(cancellationToken).ConfigureAwait(false);
            var functionOutputItems = functionResults.Select(fr => ResponseItem.CreateFunctionCallOutputItem(fr.CallId, fr.Result?.ToString() ?? string.Empty)).ToList();

            // If store is enabled we only need to send the function output items
            if (agent.StoreEnabled)
            {
                inputItems = [.. functionOutputItems];
            }
            else
            {
                inputItems.AddRange(functionOutputItems);
            }

            // Return the function results as a message
            ChatMessageContentItemCollection items = [.. functionResults];
            ChatMessageContent functionResultMessage = new()
            {
                Role = AuthorRole.Tool,
                Items = items,
            };
            overrideHistory.Add(functionResultMessage);
            yield return functionResultMessage;
        }
    }

    internal static async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        OpenAIResponseAgent agent,
        ChatHistory history,
        AgentThread agentThread,
        AgentInvokeOptions? options,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var responseAgentThread = agentThread as OpenAIResponseAgentThread;

        var overrideHistory = history;
        if (!agent.StoreEnabled)
        {
            // Use the thread chat history
            overrideHistory = [.. GetChatHistory(agentThread)];
        }

        var inputItems = overrideHistory.Select(m => m.ToResponseItem()).ToList();
        var creationOptions = ResponseCreationOptionsFactory.CreateOptions(agent, agentThread, options);

        FunctionCallsProcessor functionProcessor = new();
        FunctionChoiceBehaviorOptions functionOptions = new() { AllowConcurrentInvocation = true, AllowParallelCalls = true, RetainArgumentTypes = true };
        ChatMessageContent? message = null;
        for (int requestIndex = 0; ; requestIndex++)
        {
            // Make the call to the OpenAIResponseClient and process the streaming results.
            DateTimeOffset? createdAt = null;
            string? responseId = null;
            string? modelId = null;
            AuthorRole? lastRole = null;
            Dictionary<int, MessageResponseItem> outputIndexToMessages = [];
            Dictionary<int, FunctionCallInfo>? functionCallInfos = null;
            StreamingFunctionCallUpdateContent? functionCallUpdateContent = null;
            OpenAIResponse? response = null;
            await foreach (var streamingUpdate in agent.Client.CreateResponseStreamingAsync(inputItems, creationOptions, cancellationToken).ConfigureAwait(false))
            {
                switch (streamingUpdate)
                {
                    case StreamingResponseCreatedUpdate createdUpdate:
                        createdAt = createdUpdate.Response.CreatedAt;
                        responseId = createdUpdate.Response.Id;
                        modelId = createdUpdate.Response.Model;
                        break;

                    case StreamingResponseCompletedUpdate completedUpdate:
                        response = completedUpdate.Response;
                        message = completedUpdate.Response.ToChatMessageContent();
                        overrideHistory.Add(message);
                        break;

                    case StreamingResponseOutputItemAddedUpdate outputItemAddedUpdate:
                        switch (outputItemAddedUpdate.Item)
                        {
                            case MessageResponseItem mri:
                                outputIndexToMessages[outputItemAddedUpdate.OutputIndex] = mri;
                                break;

                            case FunctionCallResponseItem fcri:
                                (functionCallInfos ??= [])[outputItemAddedUpdate.OutputIndex] = new(fcri);
                                break;
                        }

                        break;

                    case StreamingResponseOutputItemDoneUpdate outputItemDoneUpdate:
                        _ = outputIndexToMessages.Remove(outputItemDoneUpdate.OutputIndex);
                        break;

                    case StreamingResponseOutputTextDeltaUpdate outputTextDeltaUpdate:
                        _ = outputIndexToMessages.TryGetValue(outputTextDeltaUpdate.OutputIndex, out MessageResponseItem? messageItem);
                        lastRole = messageItem?.Role.ToAuthorRole();
                        yield return outputTextDeltaUpdate.ToStreamingChatMessageContent(modelId, lastRole);

                        break;

                    case StreamingResponseFunctionCallArgumentsDeltaUpdate functionCallArgumentsDeltaUpdate:
                    {
                        if (functionCallInfos?.TryGetValue(functionCallArgumentsDeltaUpdate.OutputIndex, out FunctionCallInfo? callInfo) is true)
                        {
                            _ = (callInfo.Arguments ??= new()).Append(functionCallArgumentsDeltaUpdate.Delta);
                        }

                        break;
                    }

                    case StreamingResponseFunctionCallArgumentsDoneUpdate functionCallOutputDoneUpdate:
                    {
                        if (functionCallInfos?.TryGetValue(functionCallOutputDoneUpdate.OutputIndex, out FunctionCallInfo? callInfo) is true)
                        {
                            _ = functionCallInfos.Remove(functionCallOutputDoneUpdate.OutputIndex);

                            functionCallUpdateContent = callInfo.ResponseItem.ToStreamingFunctionCallUpdateContent(callInfo.Arguments?.ToString() ?? string.Empty);

                            yield return new StreamingChatMessageContent(
                                lastRole ?? AuthorRole.Assistant,
                                content: null)
                            {
                                ModelId = modelId,
                                InnerContent = functionCallOutputDoneUpdate,
                                Items = [functionCallUpdateContent],
                            };
                        }

                        break;
                    }

                    case StreamingResponseErrorUpdate errorUpdate:
                        yield return errorUpdate.ToStreamingChatMessageContent(modelId, lastRole);
                        break;

                    case StreamingResponseRefusalDoneUpdate refusalDone:
                        yield return refusalDone.ToStreamingChatMessageContent(modelId, lastRole);
                        break;
                }
            }

            // Update the response ID in the creation options
            if (responseAgentThread is not null)
            {
                creationOptions.PreviousResponseId = responseId;
                responseAgentThread.ResponseId = responseId;
            }
            else if (response is not null)
            {
                inputItems.AddRange(response.OutputItems);
            }

            // Reached maximum auto invocations
            if (requestIndex == MaximumAutoInvokeAttempts)
            {
                break;
            }

            // Check if there a function to invoke.
            if (functionCallUpdateContent is null)
            {
                break;
            }

            // Invoke functions and create function output items for results
            FunctionResultContent[] functionResults =
                await functionProcessor.InvokeFunctionCallsAsync(
                    message!,
                    (_) => true,
                    functionOptions,
                    options.GetKernel(agent),
                    isStreaming: true,
                    cancellationToken).ToArrayAsync(cancellationToken).ConfigureAwait(false);
            var functionOutputItems = functionResults.Select(fr => ResponseItem.CreateFunctionCallOutputItem(fr.CallId, fr.Result?.ToString() ?? string.Empty)).ToList();

            // If store is enabled we only need to send the function output items
            if (agent.StoreEnabled)
            {
                inputItems = [.. functionOutputItems];
            }
            else
            {
                inputItems.AddRange(functionOutputItems);
            }

            // Return the function results as a message
            ChatMessageContentItemCollection items = [.. functionResults];
            ChatMessageContent functionResultMessage = new()
            {
                Role = AuthorRole.Tool,
                Items = items,
            };
            StreamingChatMessageContent streamingFunctionResultMessage =
                new(AuthorRole.Tool,
                    content: null)
                {
                    ModelId = modelId,
                    InnerContent = functionCallUpdateContent,
                    Items = [functionCallUpdateContent],
                };
            overrideHistory.Add(functionResultMessage);
            yield return streamingFunctionResultMessage;
        }
    }

    private static ChatHistory GetChatHistory(AgentThread agentThread)
    {
        if (agentThread is ChatHistoryAgentThread chatHistoryAgentThread)
        {
            return chatHistoryAgentThread.ChatHistory;
        }

        throw new InvalidOperationException("The agent thread is not a ChatHistoryAgentThread.");
    }

    private static void ThrowIfIncompleteOrFailed(OpenAIResponseAgent agent, OpenAIResponse response)
    {
        if (response.Status == ResponseStatus.Incomplete || response.Status == ResponseStatus.Failed)
        {
            throw new KernelException(
                $"Run failed with status: `{response.Status}` for agent `{agent.Name}` with error: {response.Error.Message} or incomplete details: {response.IncompleteStatusDetails.Reason}");
        }
    }

    /// <summary>POCO representing function calling info.</summary>
    /// <remarks>Used to concatenation information for a single function call from across multiple streaming updates.</remarks>
    private sealed class FunctionCallInfo(FunctionCallResponseItem item)
    {
        public readonly FunctionCallResponseItem ResponseItem = item;
        public StringBuilder? Arguments;
    }

    private const int MaximumAutoInvokeAttempts = 128;
}
