// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
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
    public async Task<KernelAgent?> CreateAsync(Kernel kernel, AgentDefinition agentDefinition, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);

        foreach (var kernelAgentFactory in this._kernelAgentFactories)
        {
            if (kernelAgentFactory is not null)
            {
                var kernelAgent = await kernelAgentFactory.CreateAsync(kernel, agentDefinition, cancellationToken).ConfigureAwait(false);
                if (kernelAgent is not null)
                {
                    return Task.FromResult(kernelAgent).Result;
                }
            }
        }

        return Task.FromResult<KernelAgent?>(null).Result;
    }
}
