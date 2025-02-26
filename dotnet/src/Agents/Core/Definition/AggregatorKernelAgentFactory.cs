// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Provides a <see cref="KernelAgentFactory"/> which aggregates multiple kernel agent factories.
/// </summary>
public sealed class AggregatorKernelAgentFactory : KernelAgentFactory
{
    private readonly KernelAgentFactory[] _kernelAgentFactories;

    /// <summary>Initializes the instance.</summary>
    /// <param name="kernelAgentFactories">Ordered <see cref="KernelAgentFactory"/> instances to aggregate.</param>
    /// <remarks>
    /// Where multiple <see cref="KernelAgentFactory"/> instances are provided, the first factory that supports the <see cref="AgentDefinition"/> will be used.
    /// </remarks>
    public AggregatorKernelAgentFactory(params KernelAgentFactory[] kernelAgentFactories) : base(kernelAgentFactories.SelectMany(f => f.Types).ToArray())
    {
        Verify.NotNullOrEmpty(kernelAgentFactories);

        foreach (KernelAgentFactory kernelAgentFactory in kernelAgentFactories)
        {
            Verify.NotNull(kernelAgentFactory, nameof(kernelAgentFactories));
        }

        this._kernelAgentFactories = kernelAgentFactories;
    }

    /// <inheritdoc/>
    public override async Task<KernelAgent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(agentDefinition);

        foreach (var kernelAgentFactory in this._kernelAgentFactories)
        {
            if (kernelAgentFactory.IsSupported(agentDefinition))
            {
                var kernelAgent = await kernelAgentFactory.TryCreateAsync(kernel, agentDefinition, cancellationToken).ConfigureAwait(false);
                if (kernelAgent is not null)
                {
                    return kernelAgent;
                }
            }
        }

        return null;
    }
}
