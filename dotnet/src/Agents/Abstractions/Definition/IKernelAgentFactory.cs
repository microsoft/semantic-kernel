// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.Factory;

/// <summary>
/// Represents a factory for creating <see cref="KernelAgent"/> instances.
/// </summary>
public interface IKernelAgentFactory
{
    /// <summary>
    /// Tries to create a <see cref="KernelAgent"/> from the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="kernel">Kernel instance to associate with the agent.</param>
    /// <param name="agentDefinition">Definition of the agent to create.</param>
    /// <param name="result">The created agent, if null the agent type is not supported.</param>
    bool TryCreate(Kernel kernel, AgentDefinition agentDefinition, [NotNullWhen(true)] out KernelAgent? result);
}
