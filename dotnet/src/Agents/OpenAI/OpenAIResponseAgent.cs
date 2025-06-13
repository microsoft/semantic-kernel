// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Represents a <see cref="Agent"/> specialization based on OpenAI Response API.
/// </summary>
public sealed class OpenAIResponseAgent : Agent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIResponseAgent"/> class.
    /// </summary>
    /// <param name="client">The OpenAI provider for accessing the Responses API service.</param>
    public OpenAIResponseAgent(OpenAIResponseClient client)
    {
        Verify.NotNull(client);

        this.Client = client;
    }

    /// <summary>
    /// Expose client for additional use.
    /// </summary>
    public OpenAIResponseClient Client { get; }

    /// <summary>
    /// Storing of messages is enabled.
    /// </summary>
    public bool StoreEnabled { get; init; } = true;

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        AgentThread agentThread = await this.EnsureThreadExistsWithMessagesAsync(messages, thread, cancellationToken).ConfigureAwait(false);

        // Get the context contributions from the AIContextProviders.
        OpenAIAssistantAgentInvokeOptions extensionsContextOptions = await this.FinalizeInvokeOptionsAsync(messages, options, agentThread, cancellationToken).ConfigureAwait(false);

        // Invoke responses with the updated chat history.
        ChatHistory chatHistory = [.. messages];
        var invokeResults = ResponseThreadActions.InvokeAsync(
            this,
            chatHistory,
            agentThread,
            extensionsContextOptions,
            cancellationToken);

        // Notify the thread of new messages and return them to the caller.
        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            await this.NotifyThreadOfNewMessage(agentThread, result, cancellationToken).ConfigureAwait(false);
            yield return new(result, agentThread);
        }
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        AgentThread agentThread = await this.EnsureThreadExistsWithMessagesAsync(messages, thread, cancellationToken).ConfigureAwait(false);

        // Get the context contributions from the AIContextProviders.
        OpenAIAssistantAgentInvokeOptions extensionsContextOptions = await this.FinalizeInvokeOptionsAsync(messages, options, agentThread, cancellationToken).ConfigureAwait(false);

        // Invoke responses with the updated chat history.
        ChatHistory chatHistory = [.. messages];
        int messageCount = chatHistory.Count;
        var invokeResults = ResponseThreadActions.InvokeStreamingAsync(
            this,
            chatHistory,
            agentThread,
            extensionsContextOptions,
            cancellationToken);

        // Return streaming chat message content to the caller.
        await foreach (var result in invokeResults.ConfigureAwait(false))
        {
            yield return new(result, agentThread);
        }

        // Notify the thread of new messages
        for (int i = messageCount; i < chatHistory.Count; i++)
        {
            await this.NotifyThreadOfNewMessage(agentThread, chatHistory[i], cancellationToken).ConfigureAwait(false);

            if (options?.OnIntermediateMessage is not null)
            {
                await options.OnIntermediateMessage(chatHistory[i]).ConfigureAwait(false);
            }
        }
    }

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    [ExcludeFromCodeCoverage]
    protected override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        throw new NotSupportedException($"{nameof(OpenAIResponseAgent)} is not for use with {nameof(AgentChat)}.");
    }

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    [ExcludeFromCodeCoverage]
    protected override IEnumerable<string> GetChannelKeys()
    {
        throw new NotSupportedException($"{nameof(OpenAIResponseAgent)} is not for use with {nameof(AgentChat)}.");
    }

    /// <inheritdoc/>
    [Experimental("SKEXP0110")]
    [ExcludeFromCodeCoverage]
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        throw new NotSupportedException($"{nameof(OpenAIResponseAgent)} is not for use with {nameof(AgentChat)}.");
    }

    private async Task<AgentThread> EnsureThreadExistsWithMessagesAsync(ICollection<ChatMessageContent> messages, AgentThread? thread, CancellationToken cancellationToken)
    {
        if (this.StoreEnabled)
        {
            return await this.EnsureThreadExistsWithMessagesAsync(messages, thread, () => new OpenAIResponseAgentThread(this.Client), cancellationToken).ConfigureAwait(false);
        }

        return await this.EnsureThreadExistsWithMessagesAsync(messages, thread, () => new ChatHistoryAgentThread(), cancellationToken).ConfigureAwait(false);
    }

    private async Task<OpenAIAssistantAgentInvokeOptions> FinalizeInvokeOptionsAsync(ICollection<ChatMessageContent> messages, AgentInvokeOptions? options, AgentThread agentThread, CancellationToken cancellationToken)
    {
        Kernel kernel = options.GetKernel(this).Clone();

#pragma warning disable SKEXP0130  // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        AIContext providersContext = await agentThread.AIContextProviders.ModelInvokingAsync(messages, cancellationToken).ConfigureAwait(false);
        kernel.Plugins.AddFromAIContext(providersContext, "Tools");
#pragma warning restore SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

        string mergedAdditionalInstructions = FormatAdditionalInstructions(providersContext, options);
        OpenAIAssistantAgentInvokeOptions extensionsContextOptions =
            options is null ?
                new()
                {
                    AdditionalInstructions = mergedAdditionalInstructions,
                    Kernel = kernel,
                } :
                new(options)
                {
                    AdditionalInstructions = mergedAdditionalInstructions,
                    Kernel = kernel,
                };
        return extensionsContextOptions;
    }
}
