// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using MAAI = Microsoft.Agents.AI;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Exposes a Semantic Kernel Agent Framework <see cref="Agent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
/// </summary>
[Experimental("SKEXP0110")]
internal sealed class AIAgentAdapter : MAAI.AIAgent
{
    private readonly Func<AgentThread> _threadFactory;
    private readonly Func<JsonElement, JsonSerializerOptions?, AgentThread> _threadDeserializationFactory;
    private readonly Func<AgentThread, JsonSerializerOptions?, JsonElement> _threadSerializer;

    /// <summary>
    /// Initializes a new instance of the <see cref="AIAgentAdapter"/> class.
    /// </summary>
    /// <param name="semanticKernelAgent">The Semantic Kernel <see cref="Agent"/> to expose as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.</param>
    /// <param name="threadFactory">A factory method to create the required <see cref="AgentThread"/> type to use with the agent.</param>
    /// <param name="threadDeserializationFactory">A factory method to deserialize the required <see cref="AgentThread"/> type.</param>
    /// <param name="threadSerializer">A method to serialize the <see cref="AgentThread"/> type.</param>
    public AIAgentAdapter(
        Agent semanticKernelAgent,
        Func<AgentThread> threadFactory,
        Func<JsonElement, JsonSerializerOptions?, AgentThread> threadDeserializationFactory,
        Func<AgentThread, JsonSerializerOptions?, JsonElement> threadSerializer)
    {
        Throw.IfNull(semanticKernelAgent);
        Throw.IfNull(threadFactory);
        Throw.IfNull(threadDeserializationFactory);
        Throw.IfNull(threadSerializer);

        this.InnerAgent = semanticKernelAgent;
        this._threadFactory = threadFactory;
        this._threadDeserializationFactory = threadDeserializationFactory;
        this._threadSerializer = threadSerializer;
    }

    /// <summary>
    /// Gets the underlying Semantic Kernel Agent Framework <see cref="Agent"/>.
    /// </summary>
    public Agent InnerAgent { get; }

    /// <inheritdoc />
    public override MAAI.AgentThread DeserializeThread(JsonElement serializedThread, JsonSerializerOptions? jsonSerializerOptions = null)
        => new AIAgentThreadAdapter(this._threadDeserializationFactory(serializedThread, jsonSerializerOptions), this._threadSerializer);

    /// <inheritdoc />
    public override MAAI.AgentThread GetNewThread() => new AIAgentThreadAdapter(this._threadFactory(), this._threadSerializer);

    /// <inheritdoc />
    public override async Task<MAAI.AgentRunResponse> RunAsync(IEnumerable<ChatMessage> messages, MAAI.AgentThread? thread = null, MAAI.AgentRunOptions? options = null, CancellationToken cancellationToken = default)
    {
        thread ??= this.GetNewThread();
        if (thread is not AIAgentThreadAdapter typedThread)
        {
            throw new InvalidOperationException("The provided thread is not compatible with the agent. Only threads created by the agent can be used.");
        }

        List<ChatMessage> responseMessages = [];
        var invokeOptions = new AgentInvokeOptions()
        {
            OnIntermediateMessage = (msg) =>
            {
                responseMessages.Add(msg.ToChatMessage());
                return Task.CompletedTask;
            }
        };

        AgentResponseItem<ChatMessageContent>? lastResponseItem = null;
        ChatMessage? lastResponseMessage = null;
        await foreach (var responseItem in this.InnerAgent.InvokeAsync(messages.Select(x => x.ToChatMessageContent()).ToList(), typedThread.InnerThread, invokeOptions, cancellationToken).ConfigureAwait(false))
        {
            lastResponseItem = responseItem;
            lastResponseMessage = responseItem.Message.ToChatMessage();
            responseMessages.Add(lastResponseMessage);
        }

        return new MAAI.AgentRunResponse(responseMessages)
        {
            AgentId = this.InnerAgent.Id,
            RawRepresentation = lastResponseItem,
            AdditionalProperties = lastResponseMessage?.AdditionalProperties,
            CreatedAt = lastResponseMessage?.CreatedAt,
        };
    }

    /// <inheritdoc />
    public override async IAsyncEnumerable<MAAI.AgentRunResponseUpdate> RunStreamingAsync(
        IEnumerable<ChatMessage> messages,
        MAAI.AgentThread? thread = null,
        MAAI.AgentRunOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        thread ??= this.GetNewThread();
        if (thread is not AIAgentThreadAdapter typedThread)
        {
            throw new InvalidOperationException("The provided thread is not compatible with the agent. Only threads created by the agent can be used.");
        }

        await foreach (var responseItem in this.InnerAgent.InvokeAsync(messages.Select(x => x.ToChatMessageContent()).ToList(), typedThread.InnerThread, cancellationToken: cancellationToken).ConfigureAwait(false))
        {
            var chatMessage = responseItem.Message.ToChatMessage();

            yield return new MAAI.AgentRunResponseUpdate
            {
                AgentId = this.InnerAgent.Id,
                RawRepresentation = responseItem,
                AdditionalProperties = chatMessage.AdditionalProperties,
                MessageId = chatMessage.MessageId,
                Role = chatMessage.Role,
                CreatedAt = chatMessage.CreatedAt,
                Contents = chatMessage.Contents
            };
        }
    }
}
