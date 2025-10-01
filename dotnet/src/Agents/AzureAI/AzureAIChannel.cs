// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.Agents.Persistent;
using Microsoft.SemanticKernel.Agents.AzureAI.Internal;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// A <see cref="AgentChannel"/> specialization for use with <see cref="AzureAIAgent"/>.
/// </summary>
internal sealed class AzureAIChannel(PersistentAgentsClient client, string threadId)
    : AgentChannel<AzureAIAgent>
{
    /// <inheritdoc/>
    protected override async Task ReceiveAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        const string ErrorMessage = "The message could not be added to the thread due to an error response from the service.";

        foreach (ChatMessageContent message in history)
        {
            try
            {
                await AgentThreadActions.CreateMessageAsync(client, threadId, message, cancellationToken).ConfigureAwait(false);
            }
            catch (RequestFailedException ex)
            {
                throw new AgentThreadOperationException(ErrorMessage, ex);
            }
            catch (AggregateException ex)
            {
                throw new AgentThreadOperationException(ErrorMessage, ex);
            }
        }
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<(bool IsVisible, ChatMessageContent Message)> InvokeAsync(
        AzureAIAgent agent,
        CancellationToken cancellationToken)
    {
        return ActivityExtensions.RunWithActivityAsync(
            () => ModelDiagnostics.StartAgentInvocationActivity(agent.Id, agent.GetDisplayName(), agent.Description, agent.Kernel, []),
            () => AgentThreadActions.InvokeAsync(agent, client, threadId, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(AzureAIAgent agent, IList<ChatMessageContent> messages, CancellationToken cancellationToken = default)
    {
        return ActivityExtensions.RunWithActivityAsync(
            () => ModelDiagnostics.StartAgentInvocationActivity(agent.Id, agent.GetDisplayName(), agent.Description, agent.Kernel, messages),
            () => AgentThreadActions.InvokeStreamingAsync(agent, client, threadId, messages, invocationOptions: null, this.Logger, agent.Kernel, agent.Arguments, cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    protected override IAsyncEnumerable<ChatMessageContent> GetHistoryAsync(CancellationToken cancellationToken)
    {
        return AgentThreadActions.GetMessagesAsync(client, threadId, null, cancellationToken);
    }

    /// <inheritdoc/>
    protected override Task ResetAsync(CancellationToken cancellationToken = default)
    {
        return client.Threads.DeleteThreadAsync(threadId, cancellationToken);
    }

    /// <inheritdoc/>
    protected override string Serialize() { return threadId; }
}
