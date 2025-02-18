// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Agents.Factory;

namespace Microsoft.SemanticKernel.Agents.Definition;

/// <summary>
/// Provides a <see cref="IKernelAgentFactory"/> which aggregates multiple kernel agent factories.
/// </summary>
public sealed class AggregatorKernelAgentFactory : IKernelAgentFactory
{
    private readonly IKernelAgentFactory?[] _kernelAgentFactories;

    /// <summary>Initializes the instance.</summary>
    /// <param name="kernelAgentFactories">Ordered <see cref="IPromptTemplateFactory"/> instances to aggregate.</param>
    public AggregatorKernelAgentFactory(params IKernelAgentFactory[] kernelAgentFactories)
    {
        Verify.NotNullOrEmpty(kernelAgentFactories);
        foreach (IPromptTemplateFactory kernelAgentFactory in kernelAgentFactories)
        {
            Verify.NotNull(kernelAgentFactory, nameof(kernelAgentFactories));
        }

        this._kernelAgentFactories = kernelAgentFactories;
    }

    /// <inheritdoc/>
    public bool TryCreate(Kernel kernel, AgentDefinition agentDefinition, [NotNullWhen(true)] out KernelAgent? result)
    {
        Verify.NotNull(agentDefinition);

        foreach (var kernelAgentFactory in this._kernelAgentFactories)
        {
            if (kernelAgentFactory?.TryCreate(kernel, agentDefinition, out result) is true && result is not null)
            {
                return true;
            }
        }

        result = null;
        return false;
    }
}
