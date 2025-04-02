// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Provides a <see cref="AgentFactory"/> which aggregates multiple kernel agent factories.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class AggregatorKernelAgentFactory : AgentFactory
{
    private readonly AgentFactory[] _kernelAgentFactories;

    /// <summary>Initializes the instance.</summary>
    /// <param name="kernelAgentFactories">Ordered <see cref="AgentFactory"/> instances to aggregate.</param>
    /// <remarks>
    /// Where multiple <see cref="AgentFactory"/> instances are provided, the first factory that supports the <see cref="AgentDefinition"/> will be used.
    /// </remarks>
    public AggregatorKernelAgentFactory(params AgentFactory[] kernelAgentFactories) : base(kernelAgentFactories.SelectMany(f => f.Types).ToArray())
    {
        Verify.NotNullOrEmpty(kernelAgentFactories);

        foreach (AgentFactory kernelAgentFactory in kernelAgentFactories)
        {
            Verify.NotNull(kernelAgentFactory, nameof(kernelAgentFactories));
        }

        this._kernelAgentFactories = kernelAgentFactories;
    }

    /// <inheritdoc/>
    public override async Task<Agent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, AgentCreationOptions? agentCreationOptions = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);

        foreach (var kernelAgentFactory in this._kernelAgentFactories)
        {
            if (kernelAgentFactory.IsSupported(agentDefinition))
            {
                var kernelAgent = await kernelAgentFactory.TryCreateAsync(kernel, agentDefinition, agentCreationOptions, cancellationToken).ConfigureAwait(false);
                if (kernelAgent is not null)
                {
                    return kernelAgent;
                }
            }
        }

        return null;
    }
}
