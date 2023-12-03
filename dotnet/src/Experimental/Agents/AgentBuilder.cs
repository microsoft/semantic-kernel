// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Experimental.Agents.Extensions;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Fluent builder for initializing an <see cref="IAgent"/> instance.
/// </summary>
public partial class AgentBuilder
{
    private readonly AgentModel _model;

    private Kernel? _kernel;

    private readonly List<IAgent> _agents;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentBuilder"/> class.
    /// </summary>
    public AgentBuilder()
    {
        this._model = new AgentModel();
        this._agents = new List<IAgent>();
    }

    /// <summary>
    /// Builds the agent.
    /// </summary>
    /// <returns></returns>
    /// <exception cref="KernelException"></exception>
    public IAgent Build()
    {
        if (this._kernel is null)
        {
            throw new KernelException("Kernel must be defined for agent.");
        }

        foreach (var item in this._agents)
        {
            this._kernel.ImportPluginFromAgent(item);
        }

        return new Agent(this._model, this._kernel);
    }

    /// <summary>
    /// Defines the agent's name.
    /// </summary>
    /// <param name="name">The agent's name.</param>
    /// <returns></returns>
    public AgentBuilder WithName(string name)
    {
        this._model.Name = name;
        return this;
    }

    /// <summary>
    /// Defines the agent's description.
    /// </summary>
    /// <param name="description">The description.</param>
    /// <returns></returns>
    public AgentBuilder WithDescription(string description)
    {
        this._model.Description = description;
        return this;
    }

    /// <summary>
    /// Defines the agent's model.
    /// </summary>
    /// <param name="model">The model.</param>
    /// <returns></returns>
    public AgentBuilder WithModel(string model)
    {
        this._model.Model = model;
        return this;
    }

    /// <summary>
    /// Defines the agent's instructions.
    /// </summary>
    /// <param name="instructions">The instructions.</param>
    /// <returns></returns>
    public AgentBuilder WithInstructions(string instructions)
    {
        this._model.Instructions = instructions;
        return this;
    }


    /// <summary>
    /// Defines the agent's kernel.
    /// </summary>
    /// <param name="kernel"></param>
    /// <returns></returns>
    public AgentBuilder WithKernel(Kernel kernel)
    {
        this._kernel = kernel;
        return this;
    }

    /// <summary>
    /// Defines the agent's collaborative assistant.
    /// </summary>
    /// <param name="agent">The assistant to add to this agent.</param>
    /// <returns></returns>
    public AgentBuilder WithAgent(IAgent agent)
    {
        this._agents.Add(agent);
        return this;
    }

    /// <summary>
    /// Defines the agent's collaborative assistants.
    /// </summary>
    /// <param name="agents">The assistants to add to this agent.</param>
    /// <returns></returns>
    public AgentBuilder WithAgents(IEnumerable<IAgent> agents)
    {
        foreach (IAgent agent in agents)
        {
            this._agents.Add(agent);
        }

        return this;
    }
}
