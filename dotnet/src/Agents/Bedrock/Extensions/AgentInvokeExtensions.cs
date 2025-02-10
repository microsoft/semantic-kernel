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
internal static class AgentInvokeExtensions
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

        await foreach (var responseEvent in invokeAgentResponse.Completion.ToAsyncEnumerable().ConfigureAwait(false))
        {
            var chatMessageContent =
                HandleChunkEvent(agent, responseEvent) ??
                HandleFilesEvent(agent, responseEvent) ??
                HandleReturnControlEvent(agent, responseEvent) ??
                HandleTraceEvent(agent, responseEvent) ??
                throw new KernelException($"Failed to handle Bedrock Agent stream event: {responseEvent}");
            yield return chatMessageContent;
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
            var chatMessageContent =
                HandleChunkEvent(agent, responseEvent) ??
                HandleFilesEvent(agent, responseEvent) ??
                HandleReturnControlEvent(agent, responseEvent) ??
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
        return responseEvent is not FilePart files
            ? null
            : new ChatMessageContent()
            {
                Role = AuthorRole.Assistant,
                AuthorName = agent.GetDisplayName(),
                Content = "Files received",
                ModelId = agent.GetAgentModel().FoundationModel,
                InnerContent = responseEvent,
            };
    }

    private static ChatMessageContent? HandleReturnControlEvent(
        BedrockAgent agent,
        IEventStreamEvent responseEvent)
    {
        return responseEvent is not ReturnControlPayload returnControl
            ? null
            : new ChatMessageContent()
            {
                Role = AuthorRole.Assistant,
                AuthorName = agent.GetDisplayName(),
                Content = "Return control received",
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
}