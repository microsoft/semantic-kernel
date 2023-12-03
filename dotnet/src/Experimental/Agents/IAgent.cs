// Copyright (c) Microsoft. All rights reserved.

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
    /// Gets the agent's model.
    /// </summary>
    public string Model { get; }

    /// <summary>
    /// Gets the agent's instructions.
    /// </summary>
    public string Instructions { get; }

    /// <summary>
    /// A semantic-kernel <see cref="Kernel"/> instance associated with the assistant.
    /// </summary>
    internal Kernel Kernel { get; }

    /// <summary>
    /// Tools defined for run execution.
    /// </summary>
    public KernelPluginCollection Plugins { get; }

    /// <summary>
    /// The chat completion service.
    /// </summary>
    IChatCompletion ChatCompletion { get; }

    /// <summary>
    /// Create a new conversable thread.
    /// </summary>
    public IThread CreateThread(string initialUserMessage);
}
