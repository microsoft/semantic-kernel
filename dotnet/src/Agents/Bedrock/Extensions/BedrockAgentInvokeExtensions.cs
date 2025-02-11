// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgentRuntime.Model;
using Amazon.Runtime.EventStreams.Internal;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Bedrock.Extensions;

/// <summary>
/// Extensions associated with the status of a <see cref="BedrockAgent"/>.
/// </summary>
internal static class BedrockAgentInvokeExtensions
{
    public static async IAsyncEnumerable<ChatMessageContent> InternalInvokeAsync(
        this BedrockAgent agent,
        InvokeAgentRequest invokeAgentRequest,
        KernelArguments? arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var invokeAgentResponse = await agent.GetRuntimeClient().InvokeAgentAsync(invokeAgentRequest, cancellationToken).ConfigureAwait(false);

        if (invokeAgentResponse.HttpStatusCode != System.Net.HttpStatusCode.OK)
        {
            throw new HttpOperationException($"Failed to invoke agent. Status code: {invokeAgentResponse.HttpStatusCode}");
        }

        List<FunctionCallContent> functionCallContents = [];
        await foreach (var responseEvent in invokeAgentResponse.Completion.ToAsyncEnumerable().ConfigureAwait(false))
        {
            // TODO: Handle exception events
            var chatMessageContent =
                HandleChunkEvent(agent, responseEvent) ??
                HandleFilesEvent(agent, responseEvent) ??
                HandleReturnControlEvent(agent, responseEvent, arguments) ??
                HandleTraceEvent(agent, responseEvent) ??
                throw new KernelException($"Failed to handle Bedrock Agent stream event: {responseEvent}");
            if (chatMessageContent.Items.Count > 0 && chatMessageContent.Items[0] is FunctionCallContent functionCallContent)
            {
                functionCallContents.AddRange(chatMessageContent.Items.Where(item => item is FunctionCallContent).Cast<FunctionCallContent>());
            }
            else
            {
                yield return chatMessageContent;
            }
        }

        if (functionCallContents.Count > 0)
        {
            var functionResults = await InvokeFunctionCallsAsync(agent, functionCallContents, cancellationToken).ConfigureAwait(false);
            var sessionState = CreateSessionStateWithFunctionResults(functionResults);
        }
    }

    public static async IAsyncEnumerable<StreamingChatMessageContent> InternalInvokeStreamingAsync(
        this BedrockAgent agent,
        InvokeAgentRequest invokeAgentRequest,
        KernelArguments? arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var invokeAgentResponse = await agent.GetRuntimeClient().InvokeAgentAsync(invokeAgentRequest, cancellationToken).ConfigureAwait(false);

        if (invokeAgentResponse.HttpStatusCode != System.Net.HttpStatusCode.OK)
        {
            throw new HttpOperationException($"Failed to invoke agent. Status code: {invokeAgentResponse.HttpStatusCode}");
        }

        await foreach (var responseEvent in invokeAgentResponse.Completion.ToAsyncEnumerable().ConfigureAwait(false))
        {
            // TODO: Handle exception events
            var chatMessageContent =
                HandleChunkEvent(agent, responseEvent) ??
                HandleFilesEvent(agent, responseEvent) ??
                HandleReturnControlEvent(agent, responseEvent, arguments) ??
                HandleTraceEvent(agent, responseEvent) ??
                throw new KernelException($"Failed to handle Bedrock Agent stream event: {responseEvent}");
            yield return new(chatMessageContent.Role, chatMessageContent.Content)
            {
                AuthorName = chatMessageContent.AuthorName,
                ModelId = chatMessageContent.ModelId,
                InnerContent = chatMessageContent.InnerContent,
            };
        }
    }

    private static ChatMessageContent? HandleChunkEvent(
        BedrockAgent agent,
        IEventStreamEvent responseEvent)
    {
        return responseEvent is not PayloadPart payload
            ? null
            : new ChatMessageContent()
            {
                Role = AuthorRole.Assistant,
                AuthorName = agent.GetDisplayName(),
                Content = Encoding.UTF8.GetString(payload.Bytes.ToArray()),
                ModelId = agent.GetAgentModel().FoundationModel,
                InnerContent = responseEvent,
            };
    }

    private static ChatMessageContent? HandleFilesEvent(
        BedrockAgent agent,
        IEventStreamEvent responseEvent)
    {
        if (responseEvent is not FilePart files)
        {
            return null;
        }

        ChatMessageContentItemCollection binaryContents = [];
        foreach (var file in files.Files)
        {
            binaryContents.Add(new BinaryContent(file.Bytes.ToArray(), file.Type)
            {
                Metadata = new Dictionary<string, object?>()
                {
                    { "Name", file.Name },
                },
            });
        }

        return new ChatMessageContent()
        {
            Role = AuthorRole.Assistant,
            AuthorName = agent.GetDisplayName(),
            Items = binaryContents,
            ModelId = agent.GetAgentModel().FoundationModel,
            InnerContent = responseEvent,
        };
    }

    private static ChatMessageContent? HandleReturnControlEvent(
        BedrockAgent agent,
        IEventStreamEvent responseEvent,
        KernelArguments? arguments)
    {
        if (responseEvent is not ReturnControlPayload returnControlPayload)
        {
            return null;
        }

        ChatMessageContentItemCollection functionCallContents = [];
        foreach (var invocationInput in returnControlPayload.InvocationInputs)
        {
            var functionInvocationInput = invocationInput.FunctionInvocationInput;
            functionCallContents.Add(new FunctionCallContent(
                functionInvocationInput.Function,
                id: returnControlPayload.InvocationId,
                arguments: functionInvocationInput.Parameters.FromFunctionParameters(arguments))
            {
                Metadata = new Dictionary<string, object?>()
                {
                    { "ActionGroup", functionInvocationInput.ActionGroup },
                    { "ActionInvocationType", functionInvocationInput.ActionInvocationType },
                },
            });
        }

        return new ChatMessageContent()
        {
            Role = AuthorRole.Assistant,
            AuthorName = agent.GetDisplayName(),
            Items = functionCallContents,
            ModelId = agent.GetAgentModel().FoundationModel,
            InnerContent = responseEvent,
        };
    }

    private static ChatMessageContent? HandleTraceEvent(
        BedrockAgent agent,
        IEventStreamEvent responseEvent)
    {
        return responseEvent is not TracePart trace
            ? null
            : new ChatMessageContent()
            {
                Role = AuthorRole.Assistant,
                AuthorName = agent.GetDisplayName(),
                Content = "Trace received",
                ModelId = agent.GetAgentModel().FoundationModel,
                InnerContent = responseEvent,
            };
    }

    private static async Task<List<FunctionResultContent>> InvokeFunctionCallsAsync(
        BedrockAgent agent,
        List<FunctionCallContent> functionCallContents,
        CancellationToken cancellationToken)
    {
        var functionResults = await Task.WhenAll(functionCallContents.Select(async functionCallContent =>
        {
            return await functionCallContent.InvokeAsync(agent.Kernel, cancellationToken).ConfigureAwait(false);
        })).ConfigureAwait(false);

        return [.. functionResults];
    }

    private static SessionState CreateSessionStateWithFunctionResults(List<FunctionResultContent> functionResults)
    {
        return new SessionState()
        {
            ReturnControlInvocationResults = [.. functionResults.Select(functionResult =>
            {
                return new InvocationResultMember()
                {
                    FunctionResult = new()
                    {
                        ActionGroup = functionResult.Metadata!["ActionGroup"] as string,
                        Function = functionResult.FunctionName,
                        ResponseBody = {
                            {
                                "TEXT",
                                new()
                                {
                                    Body = functionResult.Result as string,
                                }
                            },
                        },
                    },
                };
            })],
        };
    }
}