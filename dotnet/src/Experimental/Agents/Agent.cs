// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Represents an agent.
/// </summary>
internal class Agent : IAgent
{
    /// <summary>
    /// The agent model.
    /// </summary>
    private readonly AgentModel _model;

    /// <summary>
    /// The kernel.
    /// </summary>
    private readonly Kernel _kernel;

    /// <summary>
    /// Gets the agent's name.
    /// </summary>
    public string? Name => this._model.Name;

    /// <summary>
    /// Gets the agent's description.
    /// </summary>
    public string? Description => this._model.Description;

    /// <summary>
    /// Gets the agent's instructions.
    /// </summary>
    public string Instructions => this._model.Instructions;

    /// <summary>
    /// Gets the tools defined for run execution.
    /// </summary>
    public KernelPluginCollection Plugins => this._kernel.Plugins;

    /// <summary>
    /// Gets the kernel.
    /// </summary>
    Kernel IAgent.Kernel => this._kernel;

    /// <summary>
    /// Gets the chat completion service.
    /// </summary>
    IChatCompletionService IAgent.ChatCompletion => this._kernel.Services.GetService<IChatCompletionService>()!;

    /// <summary>
    /// Gets the assistant threads.
    /// </summary>
    Dictionary<IAgent, IThread> IAgent.AssistantThreads { get; } = new Dictionary<IAgent, IThread>();

    /// <summary>
    /// Gets the planner.
    /// </summary>
    public string Planner => this._model.Planner!;

    /// <summary>
    /// Initializes a new instance of the <see cref="Agent"/> class.
    /// </summary>
    /// <param name="model">The model</param>
    /// <param name="kernel">The kernel</param>
    public Agent(AgentModel model,
        Kernel kernel)
    {
        this._model = model;
        this._kernel = kernel;
    }

    /// <summary>
    /// Create a new conversable thread.
    /// </summary>
    /// <returns></returns>
    public IThread CreateThread()
    {
        return new Thread(this);
    }

    /// <summary>
    /// Create a new conversable thread using actual kernel arguments.
    /// </summary>
    /// <param name="initatedAgent">The agent that is creating a thread with this agent.</param>
    /// <param name="arguments">The actual kernel parameters.</param>
    /// <returns></returns>
    IThread IAgent.CreateThread(IAgent initatedAgent, Dictionary<string, object?> arguments)
    {
        return new Thread(this, initatedAgent.Name!, arguments);
    }
}
