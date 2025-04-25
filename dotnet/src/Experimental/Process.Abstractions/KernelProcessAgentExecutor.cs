// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Represents a step in a process that executes an agent.
/// </summary>
public class KernelProcessAgentExecutor : KernelProcessStep<KernelProcessAgentExecutorState>
{
    private readonly AgentFactory? _agentFactory;
    private readonly KernelProcessAgentStep _agentStep;

    internal KernelProcessAgentExecutorState _state = new();

    /// <summary>
    /// Constructor used by parent process passing specific agent factory
    /// </summary>
    /// <param name="agentFactory"></param>
    /// <param name="agentStep"></param>
    public KernelProcessAgentExecutor(AgentFactory? agentFactory, KernelProcessAgentStep agentStep)
    {
        Verify.NotNull(agentStep);
        Verify.NotNull(agentStep.AgentDefinition);

        this._agentFactory = agentFactory;
        this._agentStep = agentStep;
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
    /// <returns></returns>
    [KernelFunction]
    public async Task<ChatMessageContent?> InvokeAsync(Kernel kernel, object? message = null)
    {
        try
        {
            if (this._agentFactory == null)
            {
                throw new KernelException("Agent factory is not set.");
            }

            ChatMessageContent? inputMessageContent = null;
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

            List<ChatMessageContent> agentResponses = [];

            if (this._state != null && this._state.AgentId != null)
            {
                this._agentStep.AgentDefinition.Id = this._state.AgentId;
            }

            Agent agent = await this._agentFactory.CreateAsync(kernel, this._agentStep.AgentDefinition).ConfigureAwait(false);
            this._state!.AgentId = agent.Id;

            AgentThread? agentThread = this._state.AgentThread;

            await foreach (var response in agent.InvokeAsync(inputMessageContent, agentThread).ConfigureAwait(false))
            {
                agentThread = response.Thread;
                agentResponses.Add(response.Message);
            }

            this._state.AgentThread = agentThread;

            return agentResponses.FirstOrDefault();
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
    public AgentThread? AgentThread { get; set; }
}
