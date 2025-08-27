// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Provides a <see cref="AgentFactory"/> which aggregates multiple agent factories.
/// </summary>
[Experimental("SKEXP0110")]
public sealed class AggregatorAgentFactory : AgentFactory
{
    private readonly AgentFactory[] _agentFactories;

    /// <summary>Initializes the instance.</summary>
    /// <param name="agentFactories">Ordered <see cref="AgentFactory"/> instances to aggregate.</param>
    /// <remarks>
    /// Where multiple <see cref="AgentFactory"/> instances are provided, the first factory that supports the <see cref="AgentDefinition"/> will be used.
    /// </remarks>
    public AggregatorAgentFactory(params AgentFactory[] agentFactories) : base(agentFactories.SelectMany(f => f.Types).ToArray())
    {
        Verify.NotNullOrEmpty(agentFactories);

        foreach (AgentFactory agentFactory in agentFactories)
        {
            Verify.NotNull(agentFactory, nameof(agentFactories));
        }

        this._agentFactories = agentFactories;
    }

    /// <inheritdoc/>
    public override async Task<Agent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, AgentCreationOptions? agentCreationOptions = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);

        foreach (var agentFactory in this._agentFactories)
        {
            if (agentFactory.IsSupported(agentDefinition))
            {
                var kernelAgent = await agentFactory.TryCreateAsync(kernel, agentDefinition, agentCreationOptions, cancellationToken).ConfigureAwait(false);
                if (kernelAgent is not null)
                {
                    return kernelAgent;
                }
            }
        }

        return null;
    }
}
