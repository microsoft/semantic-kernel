// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents a factory for creating <see cref="KernelAgent"/> instances.
/// </summary>
[ExcludeFromCodeCoverage]
[Experimental("SKEXP0110")]
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
    /// Return true if this instance of <see cref="KernelAgentFactory"/> supports creating agents from the provided <see cref="AgentDefinition"/>
    /// </summary>
    /// <param name="agentDefinition">Definition of the agent to check is supported.</param>
    public bool IsSupported(AgentDefinition agentDefinition)
    {
        return this.Types.Any(s => string.Equals(s, agentDefinition.Type, StringComparison.OrdinalIgnoreCase));
    }

    /// <summary>
    /// Create a <see cref="KernelAgent"/> from the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="kernel">Kernel instance to associate with the agent.</param>
    /// <param name="agentDefinition">Definition of the agent to create.</param>
    /// <param name="promptTemplateFactory">Optional prompt template factory.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <return>The created <see cref="KernelAgent"/>, if null the agent type is not supported.</return>
    public async Task<KernelAgent> CreateAsync(Kernel kernel, AgentDefinition agentDefinition, IPromptTemplateFactory? promptTemplateFactory = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(agentDefinition);

        var kernelAgent = await this.TryCreateAsync(kernel, agentDefinition, promptTemplateFactory, cancellationToken).ConfigureAwait(false);
        return (KernelAgent?)kernelAgent ?? throw new KernelException($"Agent type {agentDefinition.Type} is not supported.");
    }

    /// <summary>
    /// Tries to create a <see cref="KernelAgent"/> from the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="kernel">Kernel instance to associate with the agent.</param>
    /// <param name="agentDefinition">Definition of the agent to create.</param>
    /// <param name="promptTemplateFactory">Optional prompt template factory.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <return>The created <see cref="KernelAgent"/>, if null the agent type is not supported.</return>
    public abstract Task<KernelAgent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, IPromptTemplateFactory? promptTemplateFactory = null, CancellationToken cancellationToken = default);
}
