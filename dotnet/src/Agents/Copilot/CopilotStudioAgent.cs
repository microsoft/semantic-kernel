// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Agents.CopilotStudio.Client;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.CopilotStudio.Internal;

namespace Microsoft.SemanticKernel.Agents.Copilot;

/// <summary>
/// Provides a specialized <see cref="Agent"/> for the Copilot Agent service.
/// </summary>
public sealed partial class CopilotStudioAgent : Agent
{
    /// <summary>
    /// The client used to interact with the Copilot Agent service.
    /// </summary>
    public CopilotClient Client { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="CopilotStudioAgent"/> class.
    /// Unlike other types of agents in Semantic Kernel, prompt templates are not supported for Copilot agents,
    /// since Copilot agents don't support using an alternative instruction in runtime.
    /// </summary>
    /// <param name="client">A client used to interact with the Copilot Agent service.</param>
    public CopilotStudioAgent(CopilotClient client)
    {
        this.Client = client;
    }

    /// <summary>
    /// CopilotStudioAgent does not support instructions like other agents.
    /// </summary>
    internal new string? Instructions => null;

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        messages ??= [];

        if (messages.Count == 0)
        {
            throw new InvalidOperationException($"{nameof(CopilotStudioAgent)} requires a message to be invoked.");
        }

        // Create a thread if needed
        CopilotStudioAgentThread agentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new CopilotStudioAgentThread(this.Client) { Logger = this.ActiveLoggerFactory.CreateLogger<CopilotStudioAgentThread>() },
            cancellationToken).ConfigureAwait(false);

        // Invoke the agent
        IAsyncEnumerable<ChatMessageContent> invokeResults = this.InvokeInternalAsync(messages, agentThread, cancellationToken);

        // Return the results to the caller in AgentResponseItems.
        await foreach (ChatMessageContent result in invokeResults.ConfigureAwait(false))
        {
            await this.NotifyThreadOfNewMessage(agentThread, result, cancellationToken).ConfigureAwait(false);
            yield return new(result, agentThread);
        }
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(
        ICollection<ChatMessageContent> messages,
        AgentThread? thread = null,
        AgentInvokeOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        messages ??= [];

        if (messages.Count == 0)
        {
            throw new InvalidOperationException($"{nameof(CopilotStudioAgent)} requires a message to be invoked.");
        }

        // Create a thread if needed
        CopilotStudioAgentThread agentThread = await this.EnsureThreadExistsWithMessagesAsync(
            messages,
            thread,
            () => new CopilotStudioAgentThread(this.Client) { Logger = this.ActiveLoggerFactory.CreateLogger<CopilotStudioAgentThread>() },
            cancellationToken).ConfigureAwait(false);

        // Invoke the agent
        IAsyncEnumerable<ChatMessageContent> invokeResults = this.InvokeInternalAsync(messages, agentThread, cancellationToken);

        // Return the results to the caller in AgentResponseItems.
        await foreach (ChatMessageContent result in invokeResults.ConfigureAwait(false))
        {
            await this.NotifyThreadOfNewMessage(agentThread, result, cancellationToken).ConfigureAwait(false);

            if (options?.OnIntermediateMessage is not null)
            {
                await options.OnIntermediateMessage(result).ConfigureAwait(false);
            }

            StreamingChatMessageContent streamedResult = new(result.Role, content: null)
            {
                Items = [.. ContentProcessor.ConvertToStreaming(result.Items, this.Logger)],
                InnerContent = result.InnerContent,
                Metadata = result.Metadata,
            };

            yield return new(streamedResult, agentThread);
        }
    }

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys()
    {
        throw new NotSupportedException($"{nameof(CopilotStudioAgent)} is not for use with {nameof(AgentChat)}.");
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        throw new NotSupportedException($"{nameof(CopilotStudioAgent)} is not for use with {nameof(AgentChat)}.");
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        throw new NotSupportedException($"{nameof(CopilotStudioAgent)} is not for use with {nameof(AgentChat)}.");
    }

    private IAsyncEnumerable<ChatMessageContent> InvokeInternalAsync(ICollection<ChatMessageContent> messages, CopilotStudioAgentThread thread, CancellationToken cancellationToken)
    {
        string question = string.Join(Environment.NewLine, messages.Select(m => m.Content));

        return ActivityProcessor.ProcessActivity(this.Client.AskQuestionAsync(question, thread.Id, cancellationToken), this.Logger);
    }
}
