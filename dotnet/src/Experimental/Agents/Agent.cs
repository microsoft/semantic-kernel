// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents;

internal class Agent : IAgent
{
    private readonly AgentModel _model;

    private readonly Kernel _kernel;

    public string? Name => this._model.Name;

    public string? Description => this._model.Description;

    public string Instructions => this._model.Instructions;

    public KernelPluginCollection Plugins => this._kernel.Plugins;

    Kernel IAgent.Kernel => this._kernel;

    IChatCompletion IAgent.ChatCompletion => this._kernel.Services.GetService<IChatCompletion>()!;

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

    public IThread CreateThread()
    {
        return new Thread(this);
    }

    IThread IAgent.CreateThread(IAgent initatedAgent, Dictionary<string, object?> arguments)
    {
        return new Thread(this, initatedAgent.Name, arguments);
    }
}
