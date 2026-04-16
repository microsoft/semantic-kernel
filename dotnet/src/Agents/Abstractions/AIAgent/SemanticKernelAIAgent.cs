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
using MEAI = Microsoft.Extensions.AI;

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
    protected override string? IdCore => this._innerAgent.Id;

    /// <inheritdoc />
    public override string? Name => this._innerAgent.Name;

    /// <inheritdoc />
    public override string? Description => this._innerAgent.Description;

    /// <inheritdoc />
    protected override ValueTask<MAAI.AgentSession> CreateSessionCoreAsync(CancellationToken cancellationToken = default)
        => new(new SemanticKernelAIAgentSession(this._threadFactory()));

    /// <inheritdoc />
    protected override ValueTask<JsonElement> SerializeSessionCoreAsync(MAAI.AgentSession session, JsonSerializerOptions? jsonSerializerOptions = null, CancellationToken cancellationToken = default)
    {
        if (session is not SemanticKernelAIAgentSession typedSession)
        {
            throw new InvalidOperationException("The provided session is not compatible with the agent. Only sessions created by the agent can be used.");
        }

        return new(this._threadSerializer(typedSession.InnerThread, jsonSerializerOptions));
    }

    /// <inheritdoc />
    protected override ValueTask<MAAI.AgentSession> DeserializeSessionCoreAsync(JsonElement serializedState, JsonSerializerOptions? jsonSerializerOptions = null, CancellationToken cancellationToken = default)
        => new(new SemanticKernelAIAgentSession(this._threadDeserializationFactory(serializedState, jsonSerializerOptions)));

    /// <inheritdoc />
    protected override async Task<MAAI.AgentResponse> RunCoreAsync(IEnumerable<ChatMessage> messages, MAAI.AgentSession? session = null, MAAI.AgentRunOptions? options = null, CancellationToken cancellationToken = default)
    {
        session ??= await this.CreateSessionCoreAsync(cancellationToken).ConfigureAwait(false);
        if (session is not SemanticKernelAIAgentSession typedSession)
        {
            throw new InvalidOperationException("The provided session is not compatible with the agent. Only sessions created by the agent can be used.");
        }

        List<ChatMessage> responseMessages = [];
        var invokeOptions = new AgentInvokeOptions()
        {
            OnIntermediateMessage = (msg) =>
            {
                // As a backwards compatibility measure, ChatCompletionService inserts the function result
                // as a text message followed by a function result message. If we detect that pattern,
                // we must remove the text message to avoid the function result showing up in the user output.
                var chatMessage = msg.ToChatMessage();
                if (chatMessage.Role == ChatRole.Tool
                    && chatMessage.Contents.Count == 2
                    && chatMessage.Contents[0] is MEAI.TextContent textContent
                    && chatMessage.Contents[1] is MEAI.FunctionResultContent functionResultContent
                    && textContent.Text == functionResultContent.Result?.ToString())
                {
                    chatMessage.Contents.RemoveAt(0);
                }

                responseMessages.Add(chatMessage);
                return Task.CompletedTask;
            }
        };

        AgentResponseItem<ChatMessageContent>? lastResponseItem = null;
        await foreach (var responseItem in this._innerAgent.InvokeAsync(messages.Select(x => x.ToChatMessageContent()).ToList(), typedSession.InnerThread, invokeOptions, cancellationToken).ConfigureAwait(false))
        {
            lastResponseItem = responseItem;
        }

        var lastResponseMessage = lastResponseItem?.Message.ToChatMessage();

        return new MAAI.AgentResponse(responseMessages)
        {
            AgentId = this._innerAgent.Id,
            RawRepresentation = lastResponseItem,
            AdditionalProperties = lastResponseMessage?.AdditionalProperties,
            CreatedAt = lastResponseMessage?.CreatedAt,
        };
    }

    /// <inheritdoc />
    protected override async IAsyncEnumerable<MAAI.AgentResponseUpdate> RunCoreStreamingAsync(
        IEnumerable<ChatMessage> messages,
        MAAI.AgentSession? session = null,
        MAAI.AgentRunOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        session ??= await this.CreateSessionCoreAsync(cancellationToken).ConfigureAwait(false);
        if (session is not SemanticKernelAIAgentSession typedSession)
        {
            throw new InvalidOperationException("The provided session is not compatible with the agent. Only sessions created by the agent can be used.");
        }

        await foreach (var responseItem in this._innerAgent.InvokeStreamingAsync(messages.Select(x => x.ToChatMessageContent()).ToList(), typedSession.InnerThread, cancellationToken: cancellationToken).ConfigureAwait(false))
        {
            var update = responseItem.Message.ToChatResponseUpdate();

            yield return new MAAI.AgentResponseUpdate
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
    {
        Throw.IfNull(serviceType);

        return serviceKey is null && serviceType == typeof(Kernel)
        ? this._innerAgent.Kernel
        : serviceKey is null && serviceType.IsInstanceOfType(this._innerAgent)
        ? this._innerAgent
        : base.GetService(serviceType, serviceKey);
    }
}
