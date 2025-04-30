// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a step in a process that executes an agent.
/// </summary>
public partial class KernelProcessAgentExecutor : KernelProcessStep<KernelProcessAgentExecutorState>
{
    private readonly AgentFactory? _agentFactory;
    private readonly KernelProcessAgentStep _agentStep;
    private readonly KernelProcessAgentThread _processThread;

    internal KernelProcessAgentExecutorState _state = new();

    /// <summary>
    /// Constructor used by parent process passing specific agent factory
    /// </summary>
    /// <param name="agentFactory"></param>
    /// <param name="agentStep"></param>
    /// <param name="processThread"></param>
    public KernelProcessAgentExecutor(AgentFactory? agentFactory, KernelProcessAgentStep agentStep, KernelProcessAgentThread processThread)
    {
        //Verify.NotNull(agentStep);
        //Verify.NotNull(agentStep.AgentDefinition); // TODO: Fix issue

        this._agentFactory = agentFactory;
        this._agentStep = agentStep;
        this._processThread = processThread;
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

            // TODO: Is this needed?
            //if (this._state != null && this._state.AgentId != null)
            //{
            //    this._agentStep.AgentDefinition.Id = this._state.AgentId;
            //}

            Agent agent = await this._agentFactory.CreateAsync(kernel, this._agentStep.AgentDefinition).ConfigureAwait(false);
            this._state!.AgentId = agent.Id;

            var threadDefinition = this._processThread with { ThreadId = this._state.ThreadId };
            var agentThread = await this._processThread.CreateAgentThreadAsync(kernel).ConfigureAwait(false);
            this._state.ThreadId = agentThread.Id;

            await foreach (var response in agent.InvokeAsync(inputMessageContent, agentThread).ConfigureAwait(false))
            {
                agentThread = response.Thread;
                agentResponses.Add(response.Message);
            }

            return agentResponses.FirstOrDefault();
        }
        catch (System.Exception)
        {
            throw;
        }
    }
}
