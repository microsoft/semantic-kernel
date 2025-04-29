// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Process.Internal;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Represents a step in a process that executes an agent.
/// </summary>
public class KernelProcessAgentExecutor : KernelProcessStep<KernelProcessAgentExecutorState>
{
    private readonly AgentFactory? _agentFactory;
    private readonly KernelProcessAgentStep _agentStep;
    private string? _threadId;

    internal KernelProcessAgentExecutorState _state = new();

    /// <summary>
    /// Constructor used by parent process passing specific agent factory
    /// </summary>
    /// <param name="agentFactory"></param>
    /// <param name="agentStep"></param>
    /// <param name="threadId"></param>
    public KernelProcessAgentExecutor(AgentFactory? agentFactory, KernelProcessAgentStep agentStep, string? threadId)
    {
        Verify.NotNull(agentStep);
        Verify.NotNull(agentStep.AgentDefinition);

        this._agentFactory = agentFactory;
        this._agentStep = agentStep;
        this._threadId = threadId;
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

            // Create a thread if needed
            var client = kernel.Services.GetService<Azure.AI.Projects.AgentsClient>() ?? throw new KernelException("The AzureAI thread type requires an AgentsClient to be registered in the kernel.");
            if (string.IsNullOrWhiteSpace(this._state!.ThreadId))
            {
                if (this._threadId == null)
                {
                    var threadResponse = await client.CreateThreadAsync().ConfigureAwait(false);

                    // Create a transient thread
                    this._threadId = threadResponse.Value.Id;
                }

                this._state.ThreadId = this._threadId;
            }

            AgentThread? agentThread = new AzureAIAgentThread(client, this._state.ThreadId);

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
