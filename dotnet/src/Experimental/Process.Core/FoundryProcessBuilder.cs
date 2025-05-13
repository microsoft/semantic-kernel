// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A builder for creating a process that can be deployed to Azure Foundry.
/// </summary>
public class FoundryProcessBuilder<TProcessState> where TProcessState : class, new()
{
    private readonly ProcessBuilder _processBuilder;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessBuilder"/> class.
    /// </summary>
    /// <param name="id">The name of the process. This is required.</param>
    /// <param name="description">The description of the Process.</param>
    public FoundryProcessBuilder(string id, string? description = null)
    {
        this._processBuilder = new ProcessBuilder(id, description, processBuilder: null, typeof(TProcessState));
    }

    /// <summary>
    /// Adds an <see cref="AzureAIAgentThread"/> to the process.
    /// </summary>
    /// <param name="threadName">The name of the thread.</param>
    /// <param name="threadPolicy">The policy that determines the lifetime of the <see cref="AzureAIAgentThread"/></param>
    /// <returns></returns>
    public ProcessBuilder AddThread(string threadName, KernelProcessThreadLifetime threadPolicy = KernelProcessThreadLifetime.Scoped)
    {
        return this._processBuilder.AddThread<AzureAIAgentThread>(threadName, threadPolicy);
    }

    /// <summary>
    /// Adds a step to the process from a declarative agent.
    /// </summary>
    /// <param name="agentDefinition">The <see cref="AgentDefinition"/></param>
    /// <param name="defaultThread">Specifies the thread reference to be used by the agent. If not provided, the agent will create a new thread for each invocation.</param>
    /// <param name="humanInLoopMode">Specifies the human-in-the-loop mode for the agent. If not provided, the default is <see cref="HITLMode.Never"/>.</param>
    /// <param name="aliases"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    public ProcessAgentBuilder<TProcessState> AddStepFromAgent(AgentDefinition agentDefinition, string? defaultThread = null, HITLMode humanInLoopMode = HITLMode.Never, IReadOnlyList<string>? aliases = null)
    {
        Verify.NotNull(agentDefinition);
        if (agentDefinition.Type != AzureAIAgentFactory.AzureAIAgentType)
        {
            throw new ArgumentException($"The agent type '{agentDefinition.Type}' is not supported. Only '{AzureAIAgentFactory.AzureAIAgentType}' is supported.");
        }

        return this._processBuilder.AddStepFromAgent<TProcessState>(agentDefinition, defaultThread, humanInLoopMode, aliases);
    }

    /// <summary>
    /// Adds a step to the process from a declarative agent.
    /// </summary>
    /// <param name="stepId">Id of the step. If not provided, the Id will come from the agent Id.</param>
    /// <param name="agentDefinition">The <see cref="AgentDefinition"/></param>
    /// <param name="threadName">Specifies the thread reference to be used by the agent. If not provided, the agent will create a new thread for each invocation.</param>
    /// <param name="humanInLoopMode">Specifies the human-in-the-loop mode for the agent. If not provided, the default is <see cref="HITLMode.Never"/>.</param>
    /// <param name="aliases"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    public ProcessAgentBuilder<TProcessState> AddStepFromAgentProxy(string stepId, AgentDefinition agentDefinition, string? threadName = null, HITLMode humanInLoopMode = HITLMode.Never, IReadOnlyList<string>? aliases = null)
    {
        Verify.NotNullOrWhiteSpace(stepId);
        Verify.NotNull(agentDefinition);
        if (agentDefinition.Type != AzureAIAgentFactory.AzureAIAgentType)
        {
            throw new ArgumentException($"The agent type '{agentDefinition.Type}' is not supported. Only '{AzureAIAgentFactory.AzureAIAgentType}' is supported.");
        }

        return this._processBuilder.AddStepFromAgentProxy<TProcessState>(agentDefinition, threadName, stepId, humanInLoopMode, aliases);
    }

    /// <summary>
    /// Provides an instance of <see cref="ProcessEdgeBuilder"/> for defining an input edge to a process.
    /// </summary>
    /// <param name="eventId">The Id of the external event.</param>
    /// <returns>An instance of <see cref="ProcessEdgeBuilder"/></returns>
    public ProcessEdgeBuilder OnInputEvent(string eventId)
    {
        return this._processBuilder.OnInputEvent(eventId);
    }

    /// <summary>
    /// Creates a <see cref="ListenForBuilder"/> instance to define a listener for incoming messages.
    /// </summary>
    /// <returns></returns>
    public FoundryListenForBuilder ListenFor()
    {
        return new FoundryListenForBuilder(this._processBuilder);
    }

    /// <summary>
    /// Builds the process.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    /// <exception cref="NotImplementedException"></exception>
    public KernelProcess Build(KernelProcessStateMetadata? stateMetadata = null)
    {
        return this._processBuilder.Build(stateMetadata);
    }
}

/// <summary>
/// A default process state for the <see cref="FoundryProcessBuilder"/>.
/// </summary>
public class DefaultProcessState
{
}

/// <summary>
/// A builder for creating a process that can be deployed to Azure Foundry.
/// </summary>
public class FoundryProcessBuilder : FoundryProcessBuilder<DefaultProcessState>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FoundryProcessBuilder"/> class.
    /// </summary>
    /// <param name="id"></param>
    public FoundryProcessBuilder(string id) : base(id)
    {
    }
}
