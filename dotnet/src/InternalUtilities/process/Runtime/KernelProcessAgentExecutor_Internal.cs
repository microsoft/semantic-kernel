// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a step in a process that executes an agent.
/// </summary>
internal sealed class KernelProcessAgentExecutorInternal : KernelProcessStep<KernelProcessAgentExecutorState>
{
    private readonly KernelProcessAgentStep _agentStep;
    private readonly KernelProcessAgentThread _processThread;
    private readonly ProcessStateManager _stateManager;

    internal KernelProcessAgentExecutorState _state = new();

    /// <summary>
    /// Constructor used by parent process passing specific agent factory
    /// </summary>
    /// <param name="agentStep"></param>
    /// <param name="processThread"></param>
    /// <param name="stateManager"></param>
    public KernelProcessAgentExecutorInternal(KernelProcessAgentStep agentStep, KernelProcessAgentThread processThread, ProcessStateManager stateManager)
    {
        Verify.NotNull(agentStep);
        Verify.NotNull(agentStep.AgentDefinition);

        this._agentStep = agentStep;
        this._processThread = processThread;
        this._stateManager = stateManager;
    }

    /// <inheritdoc/>
    public override ValueTask ActivateAsync(KernelProcessStepState<KernelProcessAgentExecutorState> state)
    {
        this._state = state.State!;

        return base.ActivateAsync(state);
    }

    /// <summary>
    /// Invokes the agent with the provided definition.
    /// </summary>
    /// <param name="kernel">instance of <see cref="Kernel"/></param>
    /// <param name="message">incoming message to be processed by agent</param>
    /// <param name="writtenToThread"> <see langword="true"/> if the message has already been written to the thread</param>
    /// <returns></returns>
    [KernelFunction]
    public async Task<AgentInvokeOutputWrapper?> InvokeAsync(Kernel kernel, object? message = null, bool writtenToThread = false)
    {
        ChatMessageContent? inputMessageContent = null;
        try
        {
            // TODO: Update agent inputs to include messages_in, thread, user_messages, etc.
            // TODO: copy messages_in to the thread

            if (!writtenToThread)
            {
                inputMessageContent = null;
                if (message is ChatMessageContent chatMessage)
                {
                    // if receiving a chat message content, passing as is
                    inputMessageContent = chatMessage;
                }
                else
                {
                    // else wrapping it up assuming it is serializable
                    // todo: add try catch and use shared serialization logic
                    inputMessageContent = new ChatMessageContent(
                        ChatCompletion.AuthorRole.User,
                        JsonSerializer.Serialize(message)
                    );
                }
            }

            if (this._agentStep.AgentIdResolver is not null)
            {
                var state = this._stateManager.GetState();
                this._agentStep.AgentDefinition.Id = await this._agentStep.AgentIdResolver(state).ConfigureAwait(false);
                if (string.IsNullOrWhiteSpace(this._agentStep.AgentDefinition.Id))
                {
                    throw new KernelException("AgentIdResolver returned an empty agent ID");
                }
            }

            List<ChatMessageContent> agentResponses = [];
            AgentFactory agentFactory = ProcessAgentFactory.CreateAgentFactory(this._agentStep.AgentDefinition);
            Agent agent = await agentFactory.CreateAsync(kernel, this._agentStep.AgentDefinition).ConfigureAwait(false);
            this._state!.AgentId = agent.Id;

            var threadDefinition = this._processThread with { ThreadId = this._state.ThreadId };
            var agentThread = await this._processThread.CreateAgentThreadAsync(kernel).ConfigureAwait(false);
            this._state.ThreadId = agentThread.Id;

            if (inputMessageContent is null)
            {
                await foreach (var response in agent.InvokeAsync(agentThread).ConfigureAwait(false))
                {
                    agentThread = response.Thread;
                    agentResponses.Add(response.Message);
                }
            }
            else
            {
                await foreach (var response in agent.InvokeAsync(inputMessageContent, agentThread).ConfigureAwait(false))
                {
                    agentThread = response.Thread;
                    agentResponses.Add(response.Message);
                }
            }

            var outputWrapper = new AgentInvokeOutputWrapper
            {
                MessagesOut = agentResponses,
                // TODO: Events
            };

            return outputWrapper;
        }
        catch (System.Exception)
        {
            throw;
        }
    }
}

/// <summary>
/// State used by <see cref="KernelProcessAgentExecutor"/> to persist agent and thread details
/// </summary>
public sealed class KernelProcessAgentExecutorState
{
    /// <summary>
    /// Id of agent so it is reused if the same process is invoked again
    /// </summary>
    public string? AgentId { get; set; }

    /// <summary>
    /// Thread related information used for checking thread details by the specific agent
    /// </summary>
    public string? ThreadId { get; set; }
}

/// <summary>
/// Output wrapper for agent invocation.
/// </summary>
public sealed class AgentInvokeOutputWrapper
{
    /// <summary>
    /// Collection of output messages produced by agent.
    /// </summary>
    public List<ChatMessageContent> MessagesOut { get; set; } = [];

    /// <summary>
    /// Collection of events produced by agent.
    /// </summary>
    public Dictionary<string, object?>? Events { get; set; } = [];
}
