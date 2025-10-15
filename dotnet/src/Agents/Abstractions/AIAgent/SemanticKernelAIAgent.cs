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
internal sealed class SemanticKernelAIAgent : MAAI.AIAgent
{
    private readonly Agent _innerAgent;
    private readonly Func<AgentThread> _threadFactory;
    private readonly Func<JsonElement, JsonSerializerOptions?, AgentThread> _threadDeserializationFactory;
    private readonly Func<AgentThread, JsonSerializerOptions?, JsonElement> _threadSerializer;

    /// <summary>
    /// Initializes a new instance of the <see cref="SemanticKernelAIAgent"/> class.
    /// </summary>
    /// <param name="semanticKernelAgent">The Semantic Kernel <see cref="Agent"/> to expose as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.</param>
    /// <param name="threadFactory">A factory method to create the required <see cref="AgentThread"/> type to use with the agent.</param>
    /// <param name="threadDeserializationFactory">A factory method to deserialize the required <see cref="AgentThread"/> type.</param>
    /// <param name="threadSerializer">A method to serialize the <see cref="AgentThread"/> type.</param>
    public SemanticKernelAIAgent(
        Agent semanticKernelAgent,
        Func<AgentThread> threadFactory,
        Func<JsonElement, JsonSerializerOptions?, AgentThread> threadDeserializationFactory,
        Func<AgentThread, JsonSerializerOptions?, JsonElement> threadSerializer)
    {
        Throw.IfNull(semanticKernelAgent);
        Throw.IfNull(threadFactory);
        Throw.IfNull(threadDeserializationFactory);
        Throw.IfNull(threadSerializer);

        this._innerAgent = semanticKernelAgent;
        this._threadFactory = threadFactory;
        this._threadDeserializationFactory = threadDeserializationFactory;
        this._threadSerializer = threadSerializer;
    }

    /// <inheritdoc />
    public override string Id => this._innerAgent.Id;

    /// <inheritdoc />
    public override string? Name => this._innerAgent.Name;

    /// <inheritdoc />
    public override string? Description => this._innerAgent.Description;

    /// <inheritdoc />
    public override MAAI.AgentThread DeserializeThread(JsonElement serializedThread, JsonSerializerOptions? jsonSerializerOptions = null)
        => new SemanticKernelAIAgentThread(this._threadDeserializationFactory(serializedThread, jsonSerializerOptions), this._threadSerializer);

    /// <inheritdoc />
    public override MAAI.AgentThread GetNewThread() => new SemanticKernelAIAgentThread(this._threadFactory(), this._threadSerializer);

    /// <inheritdoc />
    public override async Task<MAAI.AgentRunResponse> RunAsync(IEnumerable<ChatMessage> messages, MAAI.AgentThread? thread = null, MAAI.AgentRunOptions? options = null, CancellationToken cancellationToken = default)
    {
        thread ??= this.GetNewThread();
        if (thread is not SemanticKernelAIAgentThread typedThread)
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
        await foreach (var responseItem in this._innerAgent.InvokeAsync(messages.Select(x => x.ToChatMessageContent()).ToList(), typedThread.InnerThread, invokeOptions, cancellationToken).ConfigureAwait(false))
        {
            lastResponseItem = responseItem;
            lastResponseMessage = responseItem.Message.ToChatMessage();
            responseMessages.Add(lastResponseMessage);
        }

        return new MAAI.AgentRunResponse(responseMessages)
        {
            AgentId = this._innerAgent.Id,
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
        if (thread is not SemanticKernelAIAgentThread typedThread)
        {
            throw new InvalidOperationException("The provided thread is not compatible with the agent. Only threads created by the agent can be used.");
        }

        await foreach (var responseItem in this._innerAgent.InvokeStreamingAsync(messages.Select(x => x.ToChatMessageContent()).ToList(), typedThread.InnerThread, cancellationToken: cancellationToken).ConfigureAwait(false))
        {
            var update = responseItem.Message.ToChatResponseUpdate();

            yield return new MAAI.AgentRunResponseUpdate
            {
                AuthorName = update.AuthorName,
                AgentId = this._innerAgent.Id,
                RawRepresentation = responseItem,
                AdditionalProperties = update.AdditionalProperties,
                MessageId = update.MessageId,
                Role = update.Role,
                ResponseId = update.ResponseId,
                CreatedAt = update.CreatedAt,
                Contents = update.Contents
            };
        }
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
        => serviceKey is null && Throw.IfNull(serviceType) == typeof(Kernel)
        ? this._innerAgent.Kernel
        : serviceKey is null && serviceType.IsInstanceOfType(this._innerAgent)
        ? this._innerAgent
        : base.GetService(serviceType, serviceKey);
}
