// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Interface for an agent that can call the model and use tools.
/// </summary>
public interface IAgent
{
    /// <summary>
    /// Gets the agent's name.
    /// </summary>
    public string? Name { get; }

    /// <summary>
    /// Gets the agent's description.
    /// </summary>
    public string? Description { get; }

    /// <summary>
    /// Gets the agent's instructions.
    /// </summary>
    public string Instructions { get; }

    /// <summary>
    /// A semantic-kernel <see cref="Kernel"/> instance associated with the assistant.
    /// </summary>
    internal Kernel Kernel { get; }

    /// <summary>
    /// The chat completion service.
    /// </summary>
    internal IChatCompletion ChatCompletion { get; }

    /// <summary>
    /// Tools defined for run execution.
    /// </summary>
    public KernelPluginCollection Plugins { get; }

    /// <summary>
    /// Create a new conversable thread.
    /// </summary>
    public IThread CreateThread();

    /// <summary>
    /// Create a new conversable thread using actual kernel arguments.
    /// </summary>
    internal IThread CreateThread(IAgent initatedAgent, Dictionary<string, object?> arguments);
}
