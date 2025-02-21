// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents a factory for creating <see cref="KernelAgent"/> instances.
/// </summary>
public abstract class KernelAgentFactory
{
    /// <summary>
    /// Gets the types of agents this factory can create.
    /// </summary>
    public IReadOnlyList<string> Types { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelAgentFactory"/> class.
    /// </summary>
    /// <param name="types">Types of agent this factory can create</param>
    protected KernelAgentFactory(string[] types)
    {
        this.Types = types;
    }

    /// <summary>
    /// Tries to create a <see cref="KernelAgent"/> from the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="kernel">Kernel instance to associate with the agent.</param>
    /// <param name="agentDefinition">Definition of the agent to create.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <return>The created <see cref="KernelAgent"/>, if null the agent type is not supported.</return>
    public abstract Task<KernelAgent?> CreateAsync(Kernel kernel, AgentDefinition agentDefinition, CancellationToken cancellationToken = default);
}
